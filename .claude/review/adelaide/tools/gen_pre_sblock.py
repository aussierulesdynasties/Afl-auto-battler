"""Adelaide Oval geometry in world metres (x east, y north, z up) -> PLY files with vertex colours.
Every footprint comes from OSM (osm/geo.json); heights and profiles come from photo measurements (spec.json)."""
import json, math, sys, os
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(ROOT, 'osm/geo.json'), encoding='utf-8'))
SPEC = json.load(open(os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'spec.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'model'); os.makedirs(OUT, exist_ok=True)

def way(w): return np.array(G['ways'][str(w)], float)
PITCH = way(4681536)
PC = PITCH[:-1].mean(0)

def seg_dist(Q, P):
    """distance from points Q (n,2) to closed polyline P"""
    A = P[:-1]; B = P[1:]; D = B - A
    t = np.clip(((Q[:, None, :] - A[None]) * D[None]).sum(-1) / (D * D).sum(-1)[None], 0, 1)
    C = A[None] + t[..., None] * D[None]
    return np.sqrt(((Q[:, None, :] - C) ** 2).sum(-1)).min(1)

def densify(P, step):
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]; n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(n): out.append(a + (b - a) * k / n)
    return np.array(out)

def fill(P, step):
    """constrained-ish triangulation of polygon P (closed) with interior grid"""
    path = Path(P)
    B = densify(P, step)
    lo, hi = P.min(0), P.max(0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    I = np.c_[gx.ravel(), gy.ravel()]
    I = I[path.contains_points(I)]
    if len(I): I = I[seg_dist(I, P) > step * 0.4]
    V = np.r_[B, I]
    T = Delaunay(V).simplices
    cen = V[T].mean(1)
    T = T[path.contains_points(cen)]
    return V, T

KIND = {'plain': 0, 'seats': 1, 'concrete': 2, 'roof': 3, 'steel': 4, 'glass': 5, 'brick': 6, 'grass': 7, 'fins': 8, 'timber': 9}
class Mesh:
    """vertices carry colour, a material kind (alpha channel) and UVs in metres (s, t) for the hand-made shaders"""
    def __init__(s): s.v = []; s.c = []; s.f = []; s.uv = []; s.k = []
    def add(s, V, F, C, UV=None, kind='plain'):
        V = [tuple(x) for x in V]; o = len(s.v); s.v += V; s.c += [tuple(x) for x in C]
        s.uv += [tuple(x) for x in UV] if UV is not None else [(x[0], x[1]) for x in V]
        s.k += [KIND[kind]] * len(V) if isinstance(kind, str) else [KIND[x] for x in kind]; s.f += [tuple(o + i for i in f) for f in F]
    def save(s, name):
        hdr = ['ply', 'format ascii 1.0', 'element vertex %d' % len(s.v)] + ['property float ' + c for c in 'xyzst'] + ['property uchar ' + c for c in ('red', 'green', 'blue', 'alpha')] + ['element face %d' % len(s.f), 'property list uchar int vertex_indices', 'end_header']
        with open(os.path.join(OUT, name + '.ply'), 'w', newline='') as fh:
            fh.write(chr(10).join(hdr) + chr(10))
            for v, uv, c, k in zip(s.v, s.uv, s.c, s.k):
                fh.write('%.3f %.3f %.3f %.3f %.3f %d %d %d %d' % (*v, *uv, *[int(max(0, min(255, x))) for x in c], k * 20) + chr(10))
            for f in s.f: fh.write('%d %s' % (len(f), ' '.join(map(str, f))) + chr(10))

def arc_uv(V2, d):
    """UV for stand/roof surfaces: u = arc length round the pitch centre at this distance, v = distance from the boundary"""
    a = np.unwrap(np.arctan2(V2[:, 1] - PC[1], V2[:, 0] - PC[0])); r = np.linalg.norm(V2 - PC, axis=1)
    return np.c_[a * r, d]

def interp(prof, d):
    prof = np.array(prof, float); return np.interp(d, prof[:, 0], prof[:, 1])

def band_colour(bands, d):
    out = np.zeros((len(d), 3))
    for i, x in enumerate(d):
        c = bands[-1][1]
        for lim, col, *_ in bands:
            if x <= lim: c = col; break
        out[i] = c
    return out

def band_kind(bands, d):
    out = []
    for x in d:
        k = bands[-1][2] if len(bands[-1]) > 2 else 'seats'
        for b in bands:
            if x <= b[0]: k = b[2] if len(b) > 2 else 'seats'; break
        out.append(k)
    return out

def ccw(P):
    a = 0.0
    for i in range(len(P) - 1): a += P[i, 0] * P[i + 1, 1] - P[i + 1, 0] * P[i, 1]
    return a > 0

def walls(m, P, ztop_fn, zbot, col, step=2.0, kind='concrete'):
    """vertical walls on every edge of P from zbot to ztop_fn(points), outward facing"""
    B = densify(P, step); B = np.r_[B, B[:1]]
    zt = ztop_fn(B); n = len(B)
    V = np.r_[np.c_[B, np.full(n, zbot)], np.c_[B, zt]]
    F = []
    flip = not ccw(P)
    for i in range(n - 1):
        q = (i, i + 1, n + i + 1, n + i)
        F.append(q[::-1] if flip else q)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))]
    m.add(V, F, np.tile(col, (len(V), 1)), np.r_[np.c_[L, np.full(n, zbot)], np.c_[L, zt]], kind)


def box(m, a, b, w, col, kind):
    """square beam of width w from point a to point b"""
    a, b = np.array(a, float), np.array(b, float); d = b - a; d /= np.linalg.norm(d)
    u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0])
    v = np.cross(u, d); h = w / 2
    off = [(-h, -h), (h, -h), (h, h), (-h, h)]
    V = [a + x * u + y * v for x, y in off] + [b + x * u + y * v for x, y in off]
    F = [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
    L = np.linalg.norm(b - a); UV = [(i * w, 0) for i in range(4)] + [(i * w, L) for i in range(4)]
    m.add(V, F, [col] * 8, UV, kind)


def open_back(m, P, zf, z0, st):
    """the back of a stand above its base wall, as photographed: the upper tier is open underneath. On edges facing
    away from the pitch: a concourse slab at z0, the raked underside rising from the slab (inset metres in) to the
    stand's back edge, and white raking struts on the facade. Other edges keep the plain upper wall."""
    ob = st['open_back']; ins = ob['inset']
    B = densify(P, 2.0); B = np.r_[B, B[:1]]; zt = zf(B); flip = not ccw(P)
    run = 0.0; nxt = ob['strut_every'] / 2
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        back = nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) >= 0.5 and zt[i] > z0 + 1 and zt[i + 1] > z0 + 1
        q = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], zt[i + 1]), (a[0], a[1], zt[i])]
        if not back:
            m.add(q, [(0, 1, 2, 3)[::-1] if flip else (0, 1, 2, 3)], [st['wall2']] * 4,
                  [(run, z0), (run + L, z0), (run + L, zt[i + 1]), (run, zt[i])], st.get('wall2_kind', 'concrete'))
            run += L; continue
        ai, bi = a - nrm * ins, b - nrm * ins
        # slab (faces up) and soffit (faces down and out): drawn both ways so face order cannot hide them
        S = [(a[0], a[1], z0), (b[0], b[1], z0), (bi[0], bi[1], z0), (ai[0], ai[1], z0)]
        m.add(S, [(0, 1, 2, 3), (3, 2, 1, 0)], [ob['slab']] * 4, [(run, 0), (run + L, 0), (run + L, ins), (run, ins)], 'concrete')
        T = [(ai[0], ai[1], z0 + 0.05), (bi[0], bi[1], z0 + 0.05), (b[0], b[1], zt[i + 1]), (a[0], a[1], zt[i])]
        m.add(T, [(0, 1, 2, 3), (3, 2, 1, 0)], [ob['soffit']] * 4, [(run, 0), (run + L, 0), (run + L, ins), (run, ins)], 'steel')
        while nxt <= run + L:  # a raking strut from the slab edge up to the back edge, leaning along the facade
            t = (nxt - run) / L; p = a + e * t; o = nrm * 0.4; zt_p = zt[i] + (zt[i + 1] - zt[i]) * t
            lean = e / (L + 1e-9) * (zt_p - z0) * 0.6
            box(m, (*(p + o), z0), (*(p + o + lean), zt_p), ob['strut_w'], ob['strut'], 'steel')
            nxt += ob['strut_every']
        run += L


def arches(m, P, zf, st):
    """ground-floor arched openings in the base wall and a sandstone string course, on edges facing away from the pitch"""
    ar = st['arches']; B = densify(P, 2.0); B = np.r_[B, B[:1]]; flip = not ccw(P); zt = zf(B)
    run = 0.0; seg = []; z0, z1 = ar['trim_z']
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        if nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) < 0.5 or min(zt[i], zt[i + 1]) < z1: run += L; continue
        o = nrm * 0.06; ta, tb = a + o, b + o
        m.add([(ta[0], ta[1], z0), (tb[0], tb[1], z0), (tb[0], tb[1], z1), (ta[0], ta[1], z1)], [(0, 1, 2, 3), (3, 2, 1, 0)],
              [ar['trim']] * 4, [(run, z0), (run + L, z0), (run + L, z1), (run, z1)], 'concrete')
        seg.append((run, L, a, e / L, nrm))
        run += L
    # arches by distance along each continuous run of back-facing wall
    runs = []
    for sg in seg:
        if runs and abs(runs[-1][-1][0] + runs[-1][-1][1] - sg[0]) < 1e-6: runs[-1].append(sg)
        else: runs.append([sg])
    r = ar['w'] / 2; zs = ar['h'] - r
    for R_ in runs:
        s0, s1 = R_[0][0], R_[-1][0] + R_[-1][1]; n = int((s1 - s0 - ar['w']) // ar['every']) + 1
        if n < 1: continue
        lead = (s1 - s0 - (n - 1) * ar['every']) / 2
        for k in range(n):
            s = s0 + lead + k * ar['every']
            st_, L, a, d, nrm = next(x for x in R_ if x[0] <= s <= x[0] + x[1])
            c = a + d * (s - st_) + nrm * 0.07
            pts = [(-r, 0.0), (r, 0.0)] + [(r * math.cos(t), zs + r * math.sin(t)) for t in np.linspace(0, math.pi, 13)]
            V = [(c[0] + d[0] * x, c[1] + d[1] * x, z) for x, z in pts]
            F = [(0, 1, 2)] + [(0, 2 + j, 3 + j) for j in range(12)]
            m.add(V, F + [f[::-1] for f in F], [ar['col']] * len(V), [(s + x, z) for x, z in pts], 'plain')


def brick_tower(m, P, bt, col):
    """a square brick shaft standing against the stand's outer wall (measured from photos A and B), squared to the wall"""
    B = densify(P, 0.5); c = np.array(bt['at'], float); i = int(np.argmin(np.linalg.norm(B - c, axis=1)))
    t = B[min(i + 1, len(B) - 1)] - B[max(i - 1, 0)]; t /= np.linalg.norm(t); n = np.array([t[1], -t[0]])
    if n @ (c - PC) < 0: n = -n
    h = bt['w'] / 2; ctr = B[i] + n * (h - 1.0); H = bt['h']
    Q = [ctr + t * a + n * b for a, b in ((-h, -h), (h, -h), (h, h), (-h, h))]
    for k in range(4):
        a, b = Q[k], Q[(k + 1) % 4]
        quad = [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], H), (a[0], a[1], H)]
        m.add(quad, [(0, 1, 2, 3), (3, 2, 1, 0)], [col] * 4, [(k * bt['w'], 0), ((k + 1) * bt['w'], 0), ((k + 1) * bt['w'], H), (k * bt['w'], H)], 'brick')
    m.add([(q[0], q[1], H) for q in Q], [(0, 1, 2, 3), (3, 2, 1, 0)], [(150, 146, 140)] * 4, [(0, 0), (bt['w'], 0), (bt['w'], bt['w']), (0, bt['w'])], 'concrete')

# ---------------------------------------------------------------- build
ground = Mesh()
S = SPEC
gs = S['ground']
# lawn around the stadium
R0 = gs['size']
ground.add([(-R0, -R0, 0), (R0, -R0, 0), (R0, R0, 0), (-R0, R0, 0)], [(0, 1, 2, 3)], [gs['lawn']] * 4, kind='grass')
V, T = fill(PITCH, 4.0)
ground.add(np.c_[V, np.full(len(V), 0.05)], T, [gs['pitch']] * len(V), kind='grass')
ground.save('ground')

stands = Mesh()
for st in S['stands']:
    P = way(st['way'])
    V, T = fill(P, st.get('step', 2.0))
    d = seg_dist(V, PITCH)
    z = interp(st['profile'], d)
    C = band_colour(st['bands'], d)
    # faces upward: Delaunay order is ccw in plan -> upward normal
    stands.add(np.c_[V, z], T, C, arc_uv(V, d), band_kind(st['bands'], d))
    zf = lambda B, st=st: interp(st['profile'], seg_dist(B[:, :2], PITCH))
    wb = st.get('wall_h')
    if wb:
        walls(stands, P, lambda B: np.minimum(zf(B), wb), 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'))
        if st.get('arches'): arches(stands, P, zf, st)
        for bt in st.get('brick_towers', []): brick_tower(stands, P, bt, st['wall'])
        if st.get('band'):  # dark band capping the base wall
            bh = st['band'][0]; walls(stands, P, lambda B: np.minimum(zf(B), wb + bh), wb, st['band'][1])
            if st.get('open_back'): open_back(stands, P, zf, wb + bh, st)
            else: walls(stands, P, zf, wb + bh, st['wall2'], kind=st.get('wall2_kind', 'concrete'))
        else:
            walls(stands, P, zf, wb, st['wall2'], kind=st.get('wall2_kind', 'concrete'))
    else:
        walls(stands, P, zf, 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'))
stands.save('stands')

for blk in S.get('blocks', []):
    m = Mesh(); P = way(blk['way']) if 'way' in blk else np.array(blk['poly'], float)
    if 'way' not in blk: P = np.r_[P, P[:1]]
    V, T = fill(P, 3.0)
    m.add(np.c_[V, np.full(len(V), blk['h'])], T, [blk['top']] * len(V), kind='concrete')
    walls(m, P, lambda B, h=blk['h']: np.full(len(B), h), 0.0, blk['wall'])
    m.save('block_' + blk['name'])

# roofs: heightfield over the roof footprint, lobes along the stand
for rf in S['roofs']:
    P = way(rf['way']) + np.array(rf.get('off', [0, 0]), float)
    V, T = fill(P, rf.get('step', 1.5))
    a0, a1 = rf['a0'], rf['a1']
    if rf.get('off') or rf.get('dome'):
        aa = (np.arctan2(P[:, 1] - PC[1], P[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; a0, a1 = aa.min(), aa.max()
    def roofz(V, rf=rf, a0=a0, a1=a1):
        d = seg_dist(V, PITCH)
        t = np.clip((d - rf['d0']) / (rf['d1'] - rf['d0']), 0, 1)
        ang = (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
        s = np.clip((ang - a0) / (a1 - a0), 0, 1)
        z = rf['hf'] + (rf['hb'] - rf['hf']) * interp(rf['tprof'], t)
        z = z - rf.get('dome', 0.0) * (2 * s - 1) ** 2
        if rf.get('lobes'):
            if rf.get('valleys'):
                vv = np.array(rf['valleys']); i = np.clip(np.searchsorted(vv, s) - 1, 0, len(vv) - 2)
                fr = (s - vv[i]) / (vv[i + 1] - vv[i])
            else:
                k = rf['lobes']; fr = (s * k) % 1.0
            z = z + rf['lobeA'] * np.sqrt(np.clip(np.sin(math.pi * fr), 0, 1)) * interp(rf['lobet'], t)
        return z
    z = roofz(V)
    uv = arc_uv(V, seg_dist(V, PITCH))
    m = Mesh(); m.add(np.c_[V, z], T, [rf['col']] * len(V), uv, 'roof')
    # second side (underside) so it shows from below: steel purlins under the membrane
    m.add(np.c_[V, z - 0.3], [tuple(f[::-1]) for f in T], [rf['under']] * len(V), uv, 'steel')
    # back closure: on edges facing away from the pitch, a wall from the stand top (or ground) up to the roof edge
    if rf.get('back'):
        sp = {x['way']: x for x in S['stands']}[rf['stand']]; SP = way(sp['way']); spath = Path(SP)
        B = densify(P, 1.5); B = np.r_[B, B[:1]]; zt = roofz(B[:, :2])
        inside = spath.contains_points(B)
        zb = np.where(inside, interp(sp['profile'], seg_dist(B, PITCH)), 0.0)
        zb = np.minimum(zb, zt - 0.3)
        for i in range(len(B) - 1):
            a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; nrm = np.array([e[1], -e[0]])
            if not ccw(P): nrm = -nrm  # outward side of the roof outline (right-hand normal of a ccw ring)
            if nrm @ (mid - PC) / (np.linalg.norm(nrm) * np.linalg.norm(mid - PC) + 1e-9) < 0.5: continue
            if not rf.get('back_ground', True) and not (inside[i] and inside[i + 1]): continue
            Vq = [(a[0], a[1], zb[i]), (b[0], b[1], zb[i + 1]), (b[0], b[1], zt[i + 1] - 0.2), (a[0], a[1], zt[i] - 0.2)]
            L0 = i * 1.5; m.add(Vq, [(0, 1, 2, 3), (3, 2, 1, 0)], [rf['back']] * 4,
                                [(L0, zb[i]), (L0 + 1.5, zb[i + 1]), (L0 + 1.5, zt[i + 1]), (L0, zt[i])], rf.get('back_kind', 'glass'))
    m.save('roof_' + rf['name'])

# light towers: tapered shafts + lamp heads facing the pitch centre
tw = Mesh()
TS = S['towers']
for tid, x, y in G['towers']:
    if str(tid) not in TS['ids']: continue
    H = TS['h']; r0, r1 = TS['r0'], TS['r1']; n = 16
    V = []; F = []
    for k in range(n):
        a = 2 * math.pi * k / n
        V.append((x + r0 * math.cos(a), y + r0 * math.sin(a), 0)); V.append((x + r1 * math.cos(a), y + r1 * math.sin(a), H))
    for k in range(n):
        i, j = 2 * k, 2 * ((k + 1) % n); F.append((i, j, j + 1, i + 1))
    tw.add(V, F, [TS['col']] * len(V), [(2 * math.pi * r0 * (k // 2) / n, v[2]) for k, v in enumerate(V)], 'steel')
    # head: a flat panel tilted toward the pitch
    dvec = PC - np.array([x, y]); dvec /= np.linalg.norm(dvec); side = np.array([-dvec[1], dvec[0]])
    hw, hh = TS['head_w'] / 2, TS['head_h']
    c0 = np.array([x, y]) + dvec * 0.8
    pts = []
    for sx in (-hw, hw):
        for zz in (H - hh, H + 0.5):
            lean = (zz - (H - hh)) * -0.25
            q = c0 + side * sx + dvec * lean; pts.append((q[0], q[1], zz))
    tw.add(pts, [(0, 2, 3, 1), (1, 3, 2, 0)], [TS['head']] * 4, [(0, 0), (0, hh), (2 * hw, 0), (2 * hw, hh)], 'steel')
tw.save('towers')
print('ok', OUT)
