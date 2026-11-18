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

def fill(P, step, creases=None):
    """constrained-ish triangulation of polygon P (closed) with interior grid; `creases` (n,2) are dense points along the
    roof's fold lines (valleys, profile kinks): grid points near them are dropped so triangle edges follow the folds"""
    path = Path(P)
    B = densify(P, step)
    lo, hi = P.min(0), P.max(0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    I = np.c_[gx.ravel(), gy.ravel()]
    I = I[path.contains_points(I)]
    if len(I): I = I[seg_dist(I, P) > step * 0.4]
    if creases is not None and len(creases):
        C = creases[path.contains_points(creases)]
        C = C[seg_dist(C, P) > step * 0.25]
        from scipy.spatial import cKDTree
        if len(I) and len(C): I = I[cKDTree(C).query(I)[0] > step * 0.6]
        if len(B) and len(C): C = C[cKDTree(B).query(C)[0] > step * 0.25]
        I = np.r_[I, C] if len(I) else C
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

def smooth_outline(P, rf, sig, sig_end, end_w=0.1):
    """Clean a traced roof outline: closed Gaussian smoothing along the outline, stronger at the two roof ends
    (a traced plan wiggles there, which reads as a torn membrane edge)."""
    from scipy.ndimage import gaussian_filter1d
    Q = densify(P, 0.5); Q = Q[:-1] if np.linalg.norm(Q[0] - Q[-1]) < 1e-6 else Q
    A = gaussian_filter1d(Q, sig / 0.5, axis=0, mode='wrap'); E = gaussian_filter1d(Q, sig_end / 0.5, axis=0, mode='wrap')
    aa = (np.arctan2(Q[:, 1] - PC[1], Q[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
    s = (aa - aa.min()) / (aa.max() - aa.min()); w = np.clip(1 - np.minimum(s, 1 - s) / end_w, 0, 1)
    R = A * (1 - w)[:, None] + E * w[:, None]
    # square each end off along one radial line, so the end edge is straight in plan and keeps one lobe height
    if not rf.get('square', True): return np.r_[R, R[:1]]
    rr = np.linalg.norm(R - PC, axis=1); ar = (np.arctan2(R[:, 1] - PC[1], R[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
    lo, hi = ar.min() + 3.0 / rr.mean(), ar.max() - 3.0 / rr.mean(); ar = np.clip(ar, lo, hi) + rf['amid']
    R = PC + np.c_[np.cos(ar), np.sin(ar)] * rr[:, None]
    return np.r_[R, R[:1]]

def iso_rings(P, ds, stp):
    """Points along the lines at distances `ds` from the pitch, inside footprint P: mesh rows for fill() so a
    profile kink or a colour change runs along a clean line instead of zigzagging across triangles."""
    rr = np.linalg.norm(P - PC, axis=1); rs = np.arange(rr.min() - 5, rr.max() + 5, 0.25); out = []
    for ang in np.arange(0, 2 * math.pi, stp * 0.3 / (rr.max() + 5)):
        Q = PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]; dq = seg_dist(Q, PITCH)
        if np.any(np.diff(dq) < 0): k = np.argmax(np.maximum.accumulate(dq) > dq.max() - 1e-9); dq, rq = dq[:k + 1], rs[:k + 1]
        else: rq = rs
        dq = np.maximum.accumulate(dq)
        for d in ds:
            if dq.min() < d < dq.max(): out.append(PC + np.array([np.cos(ang), np.sin(ang)]) * np.interp(d, dq, rq))
    return np.array(out) if out else None

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

def walls(m, P, ztop_fn, zbot, col, step=2.0, kind='concrete', skip=None):
    """vertical walls on every edge of P from zbot to ztop_fn(points), outward facing; skip = boxes [x0,y0,x1,y1]
    where another model (the hotel) is the stand's outer face"""
    B = densify(P, step); B = np.r_[B, B[:1]]
    zt = ztop_fn(B); n = len(B)
    V = np.r_[np.c_[B, np.full(n, zbot)], np.c_[B, zt]]
    F = []
    flip = not ccw(P)
    for i in range(n - 1):
        mid = (B[i] + B[i + 1]) / 2
        if skip and any(b[0] <= mid[0] <= b[2] and b[1] <= mid[1] <= b[3] for b in skip): continue
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
        if back and in_block(st, mid):
            run += L
            while nxt <= run: nxt += ob['strut_every']
            continue
        q = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], zt[i + 1]), (a[0], a[1], zt[i])]
        if not back:
            if max(zt[i], zt[i + 1]) <= z0 + 0.01: run += L; continue  # the stand is below the base wall here (pitch side)
            q = [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], max(zt[i + 1], z0)), (a[0], a[1], max(zt[i], z0))]
            m.add(q, [(0, 1, 2, 3)[::-1] if flip else (0, 1, 2, 3)], [st['wall2']] * 4,
                  [(run, z0), (run + L, z0), (run + L, zt[i + 1]), (run, zt[i])], st.get('wall2_kind', 'concrete'))
            run += L; continue
        ai, bi = a - nrm * ins, b - nrm * ins
        # slab (faces up) and soffit (faces down and out): drawn both ways so face order cannot hide them
        S = [(a[0], a[1], z0), (b[0], b[1], z0), (bi[0], bi[1], z0), (ai[0], ai[1], z0)]
        m.add(S, [(0, 1, 2, 3), (3, 2, 1, 0)], [ob['slab']] * 4, [(run, 0), (run + L, 0), (run + L, ins), (run, ins)], 'concrete')
        T = [(ai[0], ai[1], z0 + 0.05), (bi[0], bi[1], z0 + 0.05), (b[0], b[1], zt[i + 1]), (a[0], a[1], zt[i])]
        m.add(T, [(0, 1, 2, 3), (3, 2, 1, 0)], [ob['soffit']] * 4, [(run, 0), (run + L, 0), (run + L, ins), (run, ins)], 'steel')
        while nxt < run: nxt += ob['strut_every']  # catch up after edges without struts
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
        if nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) < 0.5 or min(zt[i], zt[i + 1]) < z1 or in_block(st, mid): run += L; continue
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

def stand_poly(st):
    """stand outline; traced notches at corners (way_drop) stepped the seat edge and wall top, so the back runs straight there"""
    P = way(st['way'])
    if st.get('way_drop'): P = P[[i for i in range(len(P)) if i not in st['way_drop']]]
    return P


def stand_z(st, V):
    """seat height from the depth profile; a 'low_end' (east stand north tip, satellite + c07) keeps the Hill seats' low
    rake on the far side of a plan line, stepping up to the full stand within 'blend' metres"""
    z = interp(st['profile'], seg_dist(V, PITCH))
    le = st.get('low_end')
    if le:
        a, b = np.array(le['line'], float); n = np.array([-(b - a)[1], (b - a)[0]]) / np.linalg.norm(b - a)
        s = (V - a) @ n * le.get('side', 1)                       # > 0 on the low side
        w = np.clip(0.5 + s / le['blend'], 0, 1)
        z = (1 - w) * z + w * np.minimum(z, interp(le['profile'], seg_dist(V, PITCH)))
    return z


def in_block(st, mid):
    """True where a back edge belongs to the stand's separate south block (spec y range), which replaces the open back"""
    sb = st.get('south_block'); return bool(sb) and sb['y'][0] <= mid[1] <= sb['y'][1]


def south_block(m, P, st):
    """the west stand's south block between the brick towers (photos A, B, Esri): a flat-roofed building on the stand's
    outer wall with its facade in horizontal bands, a recessed floor, a glass band behind white fins, and shade sails"""
    sb = st['south_block']; B = densify(P, 2.0); B = np.r_[B, B[:1]]; flip = not ccw(P); run = 0.0
    out = sb.get('out', 0.15); H = sb['top']
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        if nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) < 0.5 or not in_block(st, mid): run += L; continue
        for z0, z1, col, kind, rec in sb['bands']:
            o = nrm * (out - rec); pa, pb = a + o, b + o
            m.add([(pa[0], pa[1], z0), (pb[0], pb[1], z0), (pb[0], pb[1], z1), (pa[0], pa[1], z1)], [(0, 1, 2, 3), (3, 2, 1, 0)],
                  [col] * 4, [(run, z0), (run + L, z0), (run + L, z1), (run, z1)], kind)
            if rec > 0:  # slab edges above and below a recessed floor
                qa, qb = a + nrm * out, b + nrm * out
                for z in (z0, z1):
                    m.add([(pa[0], pa[1], z), (pb[0], pb[1], z), (qb[0], qb[1], z), (qa[0], qa[1], z)], [(0, 1, 2, 3), (3, 2, 1, 0)],
                          [sb['slab']] * 4, [(run, 0), (run + L, 0), (run + L, rec), (run, rec)], 'concrete')
        fz = sb['fins']  # white vertical fins standing proud of the glass band
        k = math.ceil(run / fz['every']) * fz['every']
        while k < run + L:
            p = a + e * ((k - run) / L) + nrm * (out + fz['w'] / 2)
            box(m, (p[0], p[1], fz['z'][0]), (p[0], p[1], fz['z'][1]), fz['w'], fz['col'], 'steel'); k += fz['every']
        # flat roof from the facade in towards the stand
        ia, ib = a - nrm * sb['roof_in'], b - nrm * sb['roof_in']; qa, qb = a + nrm * out, b + nrm * out
        m.add([(qa[0], qa[1], H), (qb[0], qb[1], H), (ib[0], ib[1], H), (ia[0], ia[1], H)], [(0, 1, 2, 3), (3, 2, 1, 0)],
              [sb['roof_col']] * 4, [(run, 0), (run + L, 0), (run + L, sb['roof_in']), (run, sb['roof_in'])], 'concrete')
        run += L
    # shade sails: twisted tensioned sheets from the facade out over the forecourt (high and low corners alternate)
    sv = sb['sails']; segs = []
    for i in range(len(B) - 1):
        p0, p1 = B[i], B[i + 1]; mid = (p0 + p1) / 2
        if in_block(st, mid) and np.linalg.norm(mid - PC) > sv['min_r']: segs.append((p0, p1))
    def at(y):
        for p0, p1 in segs:
            if min(p0[1], p1[1]) <= y <= max(p0[1], p1[1]):
                t = (y - p0[1]) / (p1[1] - p0[1]); q = p0 + (p1 - p0) * t; e = (p1 - p0) / np.linalg.norm(p1 - p0)
                n = np.array([e[1], -e[0]]); n = n if n @ (q - PC) > 0 else -n
                return q, n
    for y0, y1 in sv['y']:
        (a, na), (b, nb) = at(y0), at(y1); o = sv['out']; zi, zo = sv['z_in'], sv['z_out']
        V = [(a[0] + na[0] * 0.2, a[1] + na[1] * 0.2, zi[0]), (b[0] + nb[0] * 0.2, b[1] + nb[1] * 0.2, zi[1]),
             (b[0] + nb[0] * o, b[1] + nb[1] * o, zo[1]), (a[0] + na[0] * o, a[1] + na[1] * o, zo[0])]
        Lw = float(np.linalg.norm(b - a))
        m.add(V, [(0, 1, 2), (0, 2, 3), (2, 1, 0), (3, 2, 0)], [sv['col']] * 4, [(0, 0), (Lw, 0), (Lw, o), (0, o)], 'plain')
        for c in (V[2], V[3]):  # posts at the outer corners
            box(m, (c[0], c[1], 0), c, 0.2, sv['post'], 'steel')

# ---------------------------------------------------------------- build
ground = Mesh()
S = SPEC
gs = S['ground']
# lawn around the stadium
R0 = gs['size']
# director: "Leave field out" - no playing field; the lawn stops at the boundary line (hole over the pitch)
SQ = np.array([(-R0, -R0), (R0, -R0), (R0, R0), (-R0, R0), (-R0, -R0)], float)
_B = np.r_[densify(SQ, 8.0), densify(PITCH, 4.0)]
_gx, _gy = np.meshgrid(np.arange(-R0, R0, 40.0), np.arange(-R0, R0, 40.0))
_I = np.c_[_gx.ravel(), _gy.ravel()]
_I = _I[~Path(PITCH).contains_points(_I)]
_I = _I[seg_dist(_I, PITCH) > 3.0]
V = np.r_[_B, _I]
T = Delaunay(V).simplices
T = T[~Path(PITCH).contains_points(V[T].mean(1))]
ground.add(np.c_[V, np.zeros(len(V))], T, [gs['lawn']] * len(V), kind='grass')
ground.save('ground')

stands = Mesh()
for st in S['stands']:
    P = stand_poly(st)
    ds = [k for k, _ in st['profile']] + [x for b in st['bands'] for x in (b[0] - 0.05, b[0] + 0.05)]
    V, T = fill(P, st.get('step', 2.0), iso_rings(P, ds, st.get('step', 2.0)))
    d = seg_dist(V, PITCH)
    z = stand_z(st, V)
    C = band_colour(st['bands'], d)
    # faces upward: Delaunay order is ccw in plan -> upward normal
    stands.add(np.c_[V, z], T, C, arc_uv(V, d), band_kind(st['bands'], d))
    zf = lambda B, st=st: stand_z(st, B[:, :2])
    wb = st.get('wall_h')
    if wb:
        walls(stands, P, lambda B: np.minimum(zf(B), wb), 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'))
        if st.get('arches'): arches(stands, P, zf, st)
        for bt in st.get('brick_towers', []): brick_tower(stands, P, bt, st['wall'])
        if st.get('south_block'): south_block(stands, P, st)
        if st.get('band'):  # dark band capping the base wall
            bh = st['band'][0]; walls(stands, P, lambda B: np.minimum(zf(B), wb + bh), wb, st['band'][1])
            if st.get('open_back'): open_back(stands, P, zf, wb + bh, st)
            else: walls(stands, P, zf, wb + bh, st['wall2'], kind=st.get('wall2_kind', 'concrete'))
        else:
            walls(stands, P, zf, wb, st['wall2'], kind=st.get('wall2_kind', 'concrete'))
    elif st.get('open_back'):  # east (photo C): wall up to the hotel roof, the upper tier's raked underside above it
        z0 = st['open_back']['z0']
        walls(stands, P, lambda B: np.minimum(zf(B), z0), 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'), skip=st.get('wall_skip'))
        open_back(stands, P, zf, z0, st)
    else:
        walls(stands, P, zf, 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'), skip=st.get('wall_skip'))
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
    if 'poly' in rf:  # outline traced from the Esri plan (lean-corrected), not OSM
        P = np.array(rf['poly'], float); P = np.r_[P, P[:1]] if np.linalg.norm(P[0] - P[-1]) > 1e-6 else P
        if rf.get('smooth'): P = smooth_outline(P, rf, *rf['smooth'])
    else:
        P = way(rf['way']) + np.array(rf.get('off', [0, 0]), float)
        if rf.get('smooth'): P = smooth_outline(P, rf, *rf['smooth'])
    a0, a1 = rf['a0'], rf['a1']
    if rf.get('off') or rf.get('dome') or 'poly' in rf:
        aa = (np.arctan2(P[:, 1] - PC[1], P[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; a0, a1 = aa.min(), aa.max()
    # fold lines of the height field: radial valley lines between lobes, and rings at the kinks of the depth profiles
    stp = rf.get('step', 1.5); cr = []; rr = np.linalg.norm(P - PC, axis=1); rlo, rhi = rr.min() - 5, rr.max() + 5
    if rf.get('lobes') and rf.get('valleys'):
        for f in rf['valleys']:
            ang = rf['amid'] + a0 + f * (a1 - a0); r = np.arange(rlo, rhi, stp * 0.3)
            cr.append(PC + np.c_[np.cos(ang) * r, np.sin(ang) * r])
    ks = [k for k, _ in rf['tprof']] + ([k for k, _ in rf['lobet']] if rf.get('lobes') else []) + [0.0, 1.0]
    ds = sorted({rf['d0'] + k * (rf['d1'] - rf['d0']) for k in ks})
    span = a1 - a0; angs = rf['amid'] + np.arange(a0 - 0.05 * span, a1 + 0.05 * span, stp * 0.3 / rhi)
    rs = np.arange(rlo, rhi, 0.25)
    for ang in angs:
        Q = PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]; dq = seg_dist(Q, PITCH)
        for d in ds:
            if dq.min() < d < dq.max(): cr.append(PC + np.array([[np.cos(ang), np.sin(ang)]]) * np.interp(d, dq, rs))
    dbk = None
    if rf.get('rim_fit'):  # front hem and back rim follow the traced outline: depth runs from the outline's own front
        from scipy.ndimage import gaussian_filter1d  # distance to its own back distance on each ray, so both edges are clean
        Bd = densify(P, 0.5); tg = np.gradient(Bd, axis=0); nr = np.c_[tg[:, 1], -tg[:, 0]] * (1 if ccw(P) else -1)
        cs = (nr * (Bd - PC)).sum(1) / (np.linalg.norm(nr, axis=1) * np.linalg.norm(Bd - PC, axis=1) + 1e-9)
        A = (np.arctan2(Bd[:, 1] - PC[1], Bd[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; Dd = seg_dist(Bd, PITCH)
        bins = np.linspace(A.min(), A.max(), 240)
        def prof(sel, red, dflt):
            idx = np.clip(np.searchsorted(bins, A[sel]), 0, len(bins) - 1); v = np.full(len(bins), np.nan)
            for k in range(len(bins)):
                if np.any(idx == k): v[k] = red(Dd[sel][idx == k])
            ok = ~np.isnan(v)
            if not ok.any(): return np.full(len(bins), dflt)
            return gaussian_filter1d(np.interp(bins, bins[ok], v[ok]), rf['rim_fit'], mode='nearest')
        dbk = (bins, prof(cs >= 0.5, np.max, rf['d1']))
        dfr = (bins, prof(cs <= -0.5, np.min, rf['d0'])) if rf.get('front_fit') else None
    else: dfr = None
    if dbk is not None:  # drop the fixed back-depth rings; put the rings on each ray's own back distance instead
        cr = []
        for ang in angs:
            Q = PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]; dq = seg_dist(Q, PITCH)
            a_rel = (ang - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; d1 = np.interp(a_rel, *dbk)
            d0 = np.interp(a_rel, *dfr) if dfr is not None else rf['d0']
            for k in sorted(set(ks)):
                d = d0 + k * (d1 - d0)
                if dq.min() < d < dq.max(): cr.append(PC + np.array([[np.cos(ang), np.sin(ang)]]) * np.interp(d, dq, rs))
    V, T = fill(P, stp, np.concatenate(cr) if cr else None)
    def roofz(V, rf=rf, a0=a0, a1=a1, dbk=dbk, dfr=dfr):
        d = seg_dist(V, PITCH)
        ang = (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
        d1 = np.interp(ang, *dbk) if dbk is not None else rf['d1']
        d0 = np.interp(ang, *dfr) if dfr is not None else rf['d0']
        t = np.clip((d - d0) / (d1 - d0), 0, 1)
        s = np.clip((ang - a0) / (a1 - a0), 0, 1)
        z = rf['hf'] + (rf['hb'] - rf['hf']) * interp(rf['tprof'], t)
        z = z - rf.get('dome', 0.0) * (2 * s - 1) ** 2
        if rf.get('lobes'):
            if rf.get('valleys'):
                vv = np.array(rf['valleys']); i = np.clip(np.searchsorted(vv, s) - 1, 0, len(vv) - 2)
                fr = (s - vv[i]) / (vv[i + 1] - vv[i])
            else:
                k = rf['lobes']; fr = (s * k) % 1.0
            amp = np.asarray(rf['lobeAs'])[i] if rf.get('lobeAs') else rf['lobeA']
            if rf.get('vz'): z = z + np.interp(s, np.array(rf['valleys']), np.array(rf['vz']))
            z = z + amp * np.sqrt(np.clip(np.sin(math.pi * fr), 0, 1)) * interp(rf['lobet'], t)
        return z
    z = roofz(V)
    uv = arc_uv(V, seg_dist(V, PITCH))
    m = Mesh(); m.add(np.c_[V, z], T, [rf['col']] * len(V), uv, 'roof')
    # second side (underside) so it shows from below: steel purlins under the membrane
    m.add(np.c_[V, z - 0.3], [tuple(f[::-1]) for f in T], [rf['under']] * len(V), uv, 'steel')
    # back closure: on edges facing away from the pitch, a wall from the stand top (or ground) up to the roof edge
    if rf.get('back'):
        sp = {x['way']: x for x in S['stands']}[rf['stand']]; SP = stand_poly(sp); spath = Path(SP)
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
    # white edge tube along the roof's back edge, and a branching prop at each valley (close/back_west_2023.jpg)
    if rf.get('trees'):
        tr = rf['trees']; B = densify(P, 1.0); B = np.r_[B, B[:1]]; zt = roofz(B[:, :2]); bk = []
        for i in range(len(B) - 1):
            a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; nrm = np.array([e[1], -e[0]])
            if not ccw(P): nrm = -nrm
            if nrm @ (mid - PC) / (np.linalg.norm(nrm) * np.linalg.norm(mid - PC) + 1e-9) < 0.5: continue
            box(m, (a[0], a[1], zt[i] - 0.2), (b[0], b[1], zt[i + 1] - 0.2), tr['tube'], tr['col'], 'steel'); bk.append(i)
        bk = np.array(bk); BA = (np.arctan2(B[bk, 1] - PC[1], B[bk, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
        sp = {x['way']: x for x in S['stands']}[rf['stand']]
        for f in rf['valleys'][1:-1]:
            j = bk[int(np.argmin(abs(BA - (a0 + f * (a1 - a0)))))]; c = B[j]
            t = B[min(j + 1, len(B) - 1)] - B[max(j - 1, 0)]; t /= np.linalg.norm(t)
            n = c - PC; n /= np.linalg.norm(n)
            SB = densify(stand_poly(sp), 0.5); base = SB[int(np.argmin(np.linalg.norm(SB - c, axis=1)))]
            zb = tr['zb'] if 'zb' in tr else sp['wall_h'] + sp['band'][0]  # props stand on the brick base, outside the upper tier
            if tr.get('fan'):  # east (photo C): two struts fan down and out from the valley point to the stand back
                for sgn in (-1, 1):
                    q = base + t * sgn * tr['span']
                    box(m, (c[0], c[1], zt[j] - 0.3), (q[0], q[1], zb), tr['arm_w'], tr['col'], 'steel')
                continue
            node = np.array([*(base + (c - base) * 0.5 + n * tr['out']), zb + (zt[j] - zb) * tr['node']])
            box(m, (base[0], base[1], zb), node, tr['col_w'], tr['col'], 'steel')
            for sgn in (-1, 1):
                q = c + t * sgn * tr['span']; k = int(np.argmin(np.linalg.norm(B[:-1] - q, axis=1)))
                box(m, node, (B[k][0], B[k][1], zt[k] - 0.3), tr['arm_w'], tr['col'], 'steel')
    # back of each petal under the rim (photo C, grid/C_petal_back.jpg): an upright glass louvre strip, then a wide white
    # eyebrow band set in under the rim
    if rf.get('eyebrow'):
        eb = rf['eyebrow']; B = densify(P, 1.0); B = np.r_[B, B[:1]]; zt = roofz(B[:, :2])
        for i in range(len(B) - 1):
            a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; nrm = np.array([e[1], -e[0]])
            if not ccw(P): nrm = -nrm
            if nrm @ (mid - PC) / (np.linalg.norm(nrm) * np.linalg.norm(mid - PC) + 1e-9) < 0.5: continue
            nn = nrm / np.linalg.norm(nrm); ai, bi = a - nn * eb['inset'], b - nn * eb['inset']
            za, zb_ = zt[i] - 0.3 - eb['tube'], zt[i + 1] - 0.3 - eb['tube']; L0 = i * 1.0
            for (top_a, top_b, h, col, kind) in ((za, zb_, eb['glass'], eb['glass_col'], 'glass'),
                                                 (za - eb['glass'], zb_ - eb['glass'], eb['band'], eb['col'], 'concrete')):
                Vq = [(ai[0], ai[1], top_a - h), (bi[0], bi[1], top_b - h), (bi[0], bi[1], top_b), (ai[0], ai[1], top_a)]
                m.add(Vq, [(0, 1, 2, 3), (3, 2, 1, 0)], [col] * 4, [(L0, 0), (L0 + 1, 0), (L0 + 1, h), (L0, h)], kind)
    m.save('roof_' + rf['name'])

# light towers (close/east_gate_2023, riverbank_2026, east_stands_2023): tapered white shaft, collar ring, a neck that
# kinks away from the pitch to a pointed tip, and a lamp frame hinged at the kink leaning over the pitch (a V in side
# view), 6 x 7 floodlights on its pitch face, a service platform at the hinge, struts between neck and frame
def cyl(m, a, b, ra, rb, col, kind, n=16):
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); d /= L
    u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0])
    v = np.cross(u, d); V = []; F = []; UV = []
    for k in range(n + 1):
        t = 2 * math.pi * k / n; e = math.cos(t) * u + math.sin(t) * v
        V += [a + ra * e, b + rb * e]; UV += [(ra * t, 0), (ra * t, L)]
    for k in range(n): i = 2 * k; F.append((i, i + 2, i + 3, i + 1))
    m.add(V, F, [col] * len(V), UV, kind)
tw = Mesh()
TS = S['towers']
for tid, x, y in G['towers']:
    if str(tid) not in TS['ids']: continue
    r0, r1 = TS['r0'], TS['r1']; Hk = TS['kink']; col = TS['col']
    d2 = PC - np.array([x, y]); d2 /= np.linalg.norm(d2); dv = np.r_[d2, 0]; sv = np.r_[-d2[1], d2[0], 0]; up = np.array([0, 0, 1.0])
    base = np.array([x, y, 0.0]); K = np.array([x, y, Hk])
    cyl(tw, base, K, r0, r1, col, 'steel')
    cz = Hk - TS['collar']; cyl(tw, (x, y, cz - 0.2), (x, y, cz + 0.2), r1 + 0.12, r1 + 0.12, col, 'steel')
    # elbow: the shaft bends back (away from the pitch), then a flat blade rises forward to a point (C close-ups)
    eb = math.radians(TS['elbow_lean']); ed = up * math.cos(eb) - dv * math.sin(eb); E = K + ed * TS['elbow_len']
    cyl(tw, K - up * 0.3, E, r1, r1 * 0.95, col, 'steel')
    ln = math.radians(TS['neck_lean']); nd = up * math.cos(ln) + dv * math.sin(ln)
    tip = E + nd * TS['neck_len']
    pd = np.cross(sv, nd)  # in the vertical plane, perpendicular to the blade
    def ring(c, dep, wid): return [c + pd * dep / 2 * a1 + sv * wid / 2 * b1 for a1, b1 in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    bl = ring(E - nd * 0.4, 2.0 * r1, 1.3 * r1) + ring(tip, 0.08, 0.06)
    tw.add(bl, [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)] + [(3, 2, 1, 0), (4, 5, 6, 7)], [col] * 8,
           [(0, 0), (1, 0), (2, 0), (3, 0), (0, 6), (1, 6), (2, 6), (3, 6)], 'steel')
    lf = ln; fd = nd   # frame runs parallel to the blade (C close-ups), on its pitch side
    fn = dv * math.cos(lf) - up * math.sin(lf)   # face aims at the pitch, down
    fw, fl = TS['frame_w'], TS['frame_len']; nc, nr = TS['cols'], TS['rows']
    F0 = E + fn * TS['frame_off']
    bow = lambda t: fn * TS['bow'] * math.sin(math.pi * t)   # the lamp bank bulges outward along its length
    gcol = TS['head']
    for i in range(nr + 1):  # frame rails across, and two side stiles
        t = i / nr; p = F0 + fd * (0.3 + (fl - 0.3) * t) + bow(t); box(tw, p - sv * fw / 2, p + sv * fw / 2, 0.14, gcol, 'steel')
    sp_ = lambda t: F0 + fd * (0.3 + (fl - 0.3) * t) + bow(t)
    for sx in (-1, 1):   # side stiles follow the bulge
        for i in range(nr): box(tw, sp_(i / nr) + sv * sx * fw / 2, sp_((i + 1) / nr) + sv * sx * fw / 2, 0.18, gcol, 'steel')
    for i in range(nr):
        for j in range(nc):
            t = (i + 0.5) / nr; p = F0 + fd * (0.3 + (fl - 0.3) * t) + bow(t) + sv * (-fw / 2 + fw * (j + 0.5) / nc)
            box(tw, p, p + fn * 0.35, 0.5, gcol, 'steel'); box(tw, p + fn * 0.35, p + fn * 0.42, 0.44, TS['lamp'], 'glass')
    for f in (0.3, 0.55, 0.8, 1.0):  # service walkways between the blade and the frame's back
        box(tw, E + nd * (0.3 + (fl - 0.3) * f), F0 + fd * (0.3 + (fl - 0.3) * f) + bow(f), 0.16, gcol, 'steel')
    P0 = E - dv * (r1 + 0.5) - up * 0.5; hw = 0.7  # small cage on the back of the elbow (photo)
    pl = P0; c = [pl + dv * a1 + sv * b1 for a1, b1 in ((-0.5, -hw), (0.5, -hw), (0.5, hw), (-0.5, hw))]
    tw.add(c, [(0, 1, 2, 3), (3, 2, 1, 0)], [gcol] * 4, [(0, 0), (1.0, 0), (1.0, 2 * hw), (0, 2 * hw)], 'steel')
    for a1, b1, a2, b2 in ((-0.5, -hw, -0.5, hw), (-0.5, -hw, 0.5, -hw), (-0.5, hw, 0.5, hw)):
        box(tw, pl + dv * a1 + sv * b1 + up * 1.0, pl + dv * a2 + sv * b2 + up * 1.0, 0.06, gcol, 'steel')
    for a1, b1 in ((-0.5, -hw), (-0.5, hw), (0.5, -hw), (0.5, hw)):
        box(tw, pl + dv * a1 + sv * b1, pl + dv * a1 + sv * b1 + up * 1.0, 0.06, gcol, 'steel')
tw.save('towers')
print('ok', OUT)
