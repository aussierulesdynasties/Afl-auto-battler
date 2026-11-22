"""Adelaide Oval geometry in world metres (x east, y north, z up) -> PLY files with vertex colours.
Every footprint comes from OSM (osm/geo.json); heights and profiles come from photo measurements (spec.json)."""
import json, math, sys, os
import functools
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

KIND = {'plain': 0, 'seats': 1, 'concrete': 2, 'roof': 3, 'steel': 4, 'glass': 5, 'brick': 6, 'grass': 7, 'fins': 8, 'timber': 9, 'copper': 10, 'stone': 11}
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
    def save_bin(s, name):
        """binary PLY (same layout as save) for the large seat mesh; all faces are quads"""
        vt = np.dtype([(c, '<f4') for c in 'xyzst'] + [(c, 'u1') for c in ('red', 'green', 'blue', 'alpha')])
        va = np.zeros(len(s.v), vt); V = np.array(s.v, float); UV = np.array(s.uv, float); C = np.clip(np.array(s.c, float), 0, 255)
        for i, c in enumerate('xyz'): va[c] = V[:, i]
        va['s'] = UV[:, 0]; va['t'] = UV[:, 1]
        for i, c in enumerate(('red', 'green', 'blue')): va[c] = C[:, i]
        va['alpha'] = np.array(s.k) * 20
        ft = np.dtype([('n', 'u1'), ('i', '<i4', (4,))]); fa = np.zeros(len(s.f), ft); fa['n'] = 4; fa['i'] = np.array(s.f)
        hdr = ['ply', 'format binary_little_endian 1.0', 'element vertex %d' % len(s.v)] + ['property float ' + c for c in 'xyzst'] + ['property uchar ' + c for c in ('red', 'green', 'blue', 'alpha')] + ['element face %d' % len(s.f), 'property list uchar int vertex_indices', 'end_header']
        with open(os.path.join(OUT, name + '.ply'), 'wb') as fh:
            fh.write((chr(10).join(hdr) + chr(10)).encode()); fh.write(va.tobytes()); fh.write(fa.tobytes())

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

def walls(m, P, ztop_fn, zbot, col, step=2.0, kind='concrete', skip=None, lift=None):
    """vertical walls on every edge of P from zbot to ztop_fn(points), outward facing; skip = boxes [x0,y0,x1,y1]
    where another model (the hotel) is the stand's outer face; lift(a, b) -> a higher base for an edge whose lower
    storey is built by something else (the west stand's arcade), or None"""
    B = densify(P, step); B = np.r_[B, B[:1]]
    zt = np.maximum(ztop_fn(B), zbot); n = len(B)
    V = np.r_[np.c_[B, np.full(n, zbot)], np.c_[B, zt]]
    F = []
    flip = not ccw(P)
    for i in range(n - 1):
        mid = (B[i] + B[i + 1]) / 2
        if skip and any(b[0] <= mid[0] <= b[2] and b[1] <= mid[1] <= b[3] for b in skip): continue
        if zt[i] <= zbot + 0.01 and zt[i + 1] <= zbot + 0.01: continue   # top below the base (the low pitch-side edge): no wall
        zl = lift(B[i], B[i + 1]) if lift else None
        if zl is not None:   # this edge's wall starts higher: its own quad, so the shared base row stays as it is
            o = len(V); a, b = B[i], B[i + 1]
            if zl >= max(zt[i], zt[i + 1]): continue
            V = np.r_[V, [(a[0], a[1], zl), (b[0], b[1], zl), (b[0], b[1], max(zt[i + 1], zl)), (a[0], a[1], max(zt[i], zl))]]
            q = (o, o + 1, o + 2, o + 3); F.append(q[::-1] if flip else q); continue
        q = (i, i + 1, n + i + 1, n + i)
        F.append(q[::-1] if flip else q)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))]
    UV = np.r_[np.c_[L, np.full(n, zbot)], np.c_[L, zt]]
    if len(V) > 2 * n: UV = np.r_[UV, [(L[int(np.argmin(np.linalg.norm(B - v[:2], axis=1)))], v[2]) for v in V[2 * n:]]]
    m.add(V, F, np.tile(col, (len(V), 1)), UV, kind)


def struts(m, P, zf, sp):
    """white steel struts in pairs leaning apart up the outside of a wall (the Riverbank stand's louvred upper
    storeys, south gate photo): every `every` m along the wall, from z0 to the stand top, `out` m proud of it"""
    B = densify(P, 1.0); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))]
    flip = 1.0 if ccw(P) else -1.0
    for s0 in np.arange(sp['every'] / 2, L[-1], sp['every']):
        i = int(np.searchsorted(L, s0)); i = min(max(i, 1), len(B) - 1)
        t = B[i] - B[i - 1]; t = t / (np.linalg.norm(t) + 1e-9); nrm = np.array([t[1], -t[0]]) * flip
        base = B[i] + nrm * sp['out']; top_z = float(zf(B[i:i + 1])[0]) - 0.3
        if top_z < sp['z0'] + 3: continue
        for sg in (-1, 1):
            a = (*(base + t * sg * 0.4), sp['z0']); b = (*(base + t * sg * sp['lean']), top_z)
            box(m, a, b, sp['w'], sp['col'], 'steel')


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
    from shapely.geometry import Polygon, Point
    from shapely.ops import nearest_points
    PP = Polygon(P).buffer(0)
    def inside(q):
        if PP.contains(Point(q)): return q
        r = nearest_points(PP.exterior, Point(q))[0]; return np.array([r.x, r.y])
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
        def inset(p):
            # the underside meets the slab where the tier above is clear of it: where a stand's back steps in (the
            # west stand's upper tier north of its middle tower) a full inset put the underside through the tread
            k = ins
            while k > 0.5 and zf(np.array([p - nrm * k]))[0] < z0 + 0.6: k -= 0.25
            return inside(p - nrm * k)
        ai, bi = inset(a), inset(b)  # at an acute corner the inset point can fall outside the end wall: keep it on the wall
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


def arcade_edge(st, a, b, zt_a, zt_b, flip, P=None):
    """True on a base-wall edge that carries the arcade: facing away from the pitch, tall enough for the string course,
    outside the south block (the entrance building has its own ground floor)"""
    ar = st['arches']; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
    nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
    if flip: nrm = -nrm
    return nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) >= 0.5 and min(zt_a, zt_b) >= ar['trim_z'][1] and not in_block(st, mid)


IVY = None   # the climbing plants over the arcade: their own part (export gives it the leaf material)


def arcade(m, P, zf, st):
    """the Western Grandstand's ground-floor arcade, built, never painted on (director 2026-11-22: the dark arches must not
    be painted on): the brick face up to the string course has real arched openings cut through it, each with brick
    reveals `depth` m deep, a dark passage behind (stairs climb inside, west_2019) and a paved floor; a sandstone beam
    crosses each opening (west_2019), the string course stands proud as a moulding with a top and underside, and the
    face carries climbing plants (Google Earth: the arcade is green with leaves, the openings clear)"""
    global IVY
    ar = st['arches']; B = densify(P, 2.0); B = np.r_[B, B[:1]]; flip = not ccw(P); zt = zf(B)
    z0, z1 = ar['trim_z']; D = ar.get('depth', 1.8); r = ar['w'] / 2; zs = ar['h'] - r
    brick, trim, dark = st['wall'], ar['trim'], ar['col']
    run = 0.0; seg = []
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; e = b - a; L = np.linalg.norm(e)
        if not arcade_edge(st, a, b, zt[i], zt[i + 1], flip): run += L; continue
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        seg.append((run, L, a, e / L, nrm)); run += L
    runs = []
    for sg in seg:
        if runs and abs(runs[-1][-1][0] + runs[-1][-1][1] - sg[0]) < 1e-6: runs[-1].append(sg)
        else: runs.append([sg])
    rng = np.random.default_rng(11)
    if IVY is None: IVY = Mesh()
    two = lambda F: F + [f[::-1] for f in F]
    for R_ in runs:
        s0, s1 = R_[0][0], R_[-1][0] + R_[-1][1]
        def at(s, off=0.0):
            st_, L, a, d, nrm = next((x for x in R_ if x[0] - 1e-6 <= s <= x[0] + x[1] + 1e-6), R_[-1])
            p = a + d * (s - st_) + nrm * off; return p, nrm
        n = int((s1 - s0 - ar['w'] - 1.0) // ar['every']) + 1
        C = []
        if n >= 1:
            lead = (s1 - s0 - (n - 1) * ar['every']) / 2; C = [s0 + lead + k * ar['every'] for k in range(n)]
        def open_bot(s, sm):   # the face's bottom at s: the ground, or the arch's crown over an opening
            for c in C:
                if abs(sm - c) < r: return zs + math.sqrt(max(0.0, r * r - (s - c) ** 2))
            return 0.0
        # the face: columns between breakpoints (edge ends, arch jambs, arch curve samples), ground or crown up to z0
        ss = {s0, s1} | {x[0] for x in R_}
        for c in C: ss |= {c + r * math.cos(t) for t in np.linspace(0, math.pi, 17)}
        ss = sorted(x for x in ss if s0 - 1e-6 <= x <= s1 + 1e-6)
        for sa, sb in zip(ss[:-1], ss[1:]):
            if sb - sa < 1e-4: continue
            sm = (sa + sb) / 2; ba, bb = open_bot(sa, sm), open_bot(sb, sm)
            (pa, _), (pb, _) = at(sa + 1e-5), at(sb - 1e-5)
            m.add([(pa[0], pa[1], ba), (pb[0], pb[1], bb), (pb[0], pb[1], z0), (pa[0], pa[1], z0)], two([(0, 1, 2, 3)]),
                  [brick] * 4, [(sa, ba), (sb, bb), (sb, z0), (sa, z0)], 'brick')
        # the string course: a moulding 0.18 m proud, with its top and underside
        for st_, L, a, d, nrm in R_:
            b = a + d * L; o = nrm * 0.18
            for q, uv in (([(a + o, z0), (b + o, z0), (b + o, z1), (a + o, z1)], [(st_, z0), (st_ + L, z0), (st_ + L, z1), (st_, z1)]),
                          ([(a, z1), (b, z1), (b + o, z1), (a + o, z1)], [(st_, 0), (st_ + L, 0), (st_ + L, 0.18), (st_, 0.18)]),
                          ([(a, z0), (b, z0), (b + o, z0), (a + o, z0)], [(st_, 0), (st_ + L, 0), (st_ + L, 0.18), (st_, 0.18)])):
                m.add([(p[0], p[1], z) for p, z in q], two([(0, 1, 2, 3)]), [trim] * 4, uv, 'stone')
        for c in C:
            # the opening's outline on the face: up one jamb, over the arch, down the other
            ol = [(c - r, 0.0)] + [(c + r * math.cos(t), zs + r * math.sin(t)) for t in np.linspace(math.pi, 0, 17)] + [(c + r, 0.0)]
            out = [at(sx)[0] for sx, _ in ol]; nr = at(c)[1]; inn = [p - nr * D for p in out]
            V = [(p[0], p[1], z) for p, (_, z) in zip(out, ol)] + [(p[0], p[1], z) for p, (_, z) in zip(inn, ol)]
            k = len(ol); F = [(j, j + 1, k + j + 1, k + j) for j in range(k - 1)]
            acc = np.r_[0, np.cumsum([math.hypot(ol[j + 1][0] - ol[j][0], ol[j + 1][1] - ol[j][1]) for j in range(k - 1)])]
            m.add(V, two(F), [brick] * len(V), [(u, 0) for u in acc] + [(u, D) for u in acc], 'brick')   # the reveals
            # the passage's back wall (in shadow) and floor
            Vb = [(p[0], p[1], z) for p, (_, z) in zip(inn, ol)]
            m.add(Vb, two([(0, j, j + 1) for j in range(1, k - 1)]), [dark] * k, [(sx, z) for sx, z in ol], 'concrete')
            fl = [inn[0], inn[-1], out[-1], out[0]]
            m.add([(p[0], p[1], 0.03) for p in fl], two([(0, 1, 2, 3)]), [(132, 128, 120)] * 4, [(0, 0), (2 * r, 0), (2 * r, D), (0, D)], 'concrete')
            # stairs climbing across the passage (west_2019): treads and risers from one jamb up toward the other
            ns = 12; hs = min(zs * 0.8, 3.6)
            for j in range(ns):
                u0, u1 = -r + 2 * r * j / ns, -r + 2 * r * (j + 1) / ns; za, zb = hs * j / ns, hs * (j + 1) / ns
                pa, pb = at(c + u0, -0.6)[0], at(c + u1, -0.6)[0]
                qa, qb = pa - nr * (D - 0.7), pb - nr * (D - 0.7)
                m.add([(pa[0], pa[1], 0.0), (pb[0], pb[1], 0.0), (pb[0], pb[1], zb), (pa[0], pa[1], zb)], two([(0, 1, 2, 3)]),
                      [(118, 116, 110)] * 4, [(u0, 0), (u1, 0), (u1, zb), (u0, zb)], 'concrete')   # the flight's side, solid
                m.add([(pa[0], pa[1], za), (qa[0], qa[1], za), (qa[0], qa[1], zb), (pa[0], pa[1], zb)], two([(0, 1, 2, 3)]),
                      [(150, 148, 142)] * 4, [(0, 0), (1, 0), (1, zb - za), (0, zb - za)], 'concrete')
                m.add([(pa[0], pa[1], zb), (qa[0], qa[1], zb), (qb[0], qb[1], zb), (pb[0], pb[1], zb)], two([(0, 1, 2, 3)]),
                      [(176, 174, 168)] * 4, [(0, 0), (1, 0), (1, 1), (0, 1)], 'concrete')
            # the sandstone beam across the opening, set in from the face (west_2019: ivy hangs off it)
            bz = ar.get('beam_z', 4.0)
            if bz + 0.45 < zs:
                pa, pb = at(c - r, -0.35)[0], at(c + r, -0.35)[0]
                box(m, (pa[0], pa[1], bz + 0.22), (pb[0], pb[1], bz + 0.22), 0.45, trim, 'stone')
        # climbing plants: leaf mats 0.12 m proud of the face over the piers and spandrels, a ragged top above the
        # string course, clear of every opening; drawn as their own part
        iv = ar.get('ivy')
        if not iv: continue
        ss2 = sorted(set(ss) | set(np.arange(s0, s1, 0.6)))
        top = {x: iv['top'] + rng.uniform(-iv['rag'], iv['rag']) for x in ss2}
        for sa, sb in zip(ss2[:-1], ss2[1:]):
            if sb - sa < 1e-4: continue
            sm = (sa + sb) / 2
            if rng.uniform() < iv.get('gap', 0.0): continue
            ba, bb = open_bot(sa, sm), open_bot(sb, sm)
            (pa, _), (pb, _) = at(sa + 1e-5, 0.12), at(sb - 1e-5, 0.12)
            ta, tb = top[sa], top[sb]
            if ta <= ba + 0.2 and tb <= bb + 0.2: continue
            # over the string course the mat steps out round the moulding
            pa2, pb2 = at(sa + 1e-5, 0.30)[0], at(sb - 1e-5, 0.30)[0]
            V = [(pa[0], pa[1], ba), (pb[0], pb[1], bb), (pb[0], pb[1], z0 - 0.05), (pa[0], pa[1], z0 - 0.05),
                 (pa2[0], pa2[1], z0), (pb2[0], pb2[1], z0), (pb2[0], pb2[1], z1), (pa2[0], pa2[1], z1),
                 (pa[0], pa[1], z1 + 0.05), (pb[0], pb[1], z1 + 0.05), (pb[0], pb[1], max(tb, z1 + 0.1)), (pa[0], pa[1], max(ta, z1 + 0.1))]
            F = [(0, 1, 2, 3), (3, 2, 5, 4), (4, 5, 6, 7), (7, 6, 9, 8), (8, 9, 10, 11)]
            IVY.add(V, two(F), [iv['col']] * len(V), [(sa if j % 4 in (0, 3) else sb, v[2]) for j, v in enumerate(V)], 'grass')


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

def parapet(m, P, zf, col=(206, 204, 198), h=1.1, step=2.0):
    """a 1.1 m upstand on every raised edge that does not face the pitch (stand ends and backs), so no seat or deck sits
    on the lip of a drop (director 2026-11-21: "chairs right on the edge of the chasm, no barrier")"""
    B = densify(P, step); B = np.r_[B, B[:1]]; zt = zf(B); flip = not ccw(P); run = 0.0
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        if nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) < -0.3 or min(zt[i], zt[i + 1]) < 3.0: run += L; continue
        q = [(a[0], a[1], zt[i]), (b[0], b[1], zt[i + 1]), (b[0], b[1], zt[i + 1] + h), (a[0], a[1], zt[i] + h)]
        m.add(q, [(0, 1, 2, 3), (3, 2, 1, 0)], [col] * 4, [(run, 0), (run + L, 0), (run + L, h), (run, h)], 'concrete')
        run += L


def front_skin(m, P, zf, col=(46, 48, 52), step=2.0):
    """the bowl's front wall at the fence, dark as in the photos (riverbank_2026, west_stands_2023: a dark wall carrying
    the LED boards), laid 2 cm proud of the stand's own wall on every pitch-facing edge"""
    B = densify(P, step); B = np.r_[B, B[:1]]; zt = zf(B); flip = not ccw(P); run = 0.0
    for i in range(len(B) - 1):
        a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; L = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0]]) / (L + 1e-9)
        if flip: nrm = -nrm
        if nrm @ (mid - PC) / (np.linalg.norm(mid - PC) + 1e-9) > -0.5: run += L; continue
        o = nrm * 0.02; pa, pb = a + o, b + o; za, zb_ = min(zt[i], 2.0), min(zt[i + 1], 2.0)
        m.add([(pa[0], pa[1], 0.0), (pb[0], pb[1], 0.0), (pb[0], pb[1], zb_), (pa[0], pa[1], za)], [(0, 1, 2, 3), (3, 2, 1, 0)],
              [col] * 4, [(run, 0), (run + L, 0), (run + L, zb_), (run, za)], 'plain')
        run += L


def corner_poly(st):
    """the lower bowl running round a corner between two stands (Esri plan: the seating is continuous at the south
    pockets): the ring from the fence out to 'depth' metres between the angles 'a' (degrees from the centre), minus the
    stands either side"""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    a0, a1 = np.radians(st['a']); A = np.linspace(a0, a1, 40)
    wedge = Polygon([tuple(PC)] + [tuple(PC + 400 * np.array([math.cos(a), math.sin(a)])) for a in A])
    ring = Polygon(PITCH).buffer(st['depth'], 64).difference(Polygon(PITCH))
    others = unary_union([Polygon(way(x['way'])).buffer(0.02) for x in SPEC['stands'] if 'way' in x])
    g = ring.intersection(wedge).difference(others)
    if g.geom_type != 'Polygon': g = max(g.geoms, key=lambda q: q.area)
    return np.array(g.simplify(0.05).exterior.coords)

def stand_poly(st):
    """stand outline; traced notches at corners (way_drop) stepped the seat edge and wall top, so the back runs straight there"""
    if 'a' in st: return corner_poly(st)
    P = way(st['way'])
    if st.get('way_drop'): P = P[[i for i in range(len(P)) if i not in st['way_drop']]]
    return P


def stand_z(st, V):
    """seat height from the depth profile; a 'low_end' (east stand north tip, satellite + c07) keeps the Hill seats' low
    rake on the far side of a plan line, stepping up to the full stand within 'blend' metres"""
    dd = seg_dist(V, PITCH); z = interp(st['profile'], dd)
    for zn in st.get('zones', []):   # a section with its own storeys (the Bradman Pavilion): its own profile inside its sweep
        k = in_sweep(pt_ang(V), zn['ang'])
        if k.any(): z[k] = interp(zn['profile'], dd[k])
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
    if 'entrance' in sb: entrance(m, B, st)


def facade_at(B, st, y, min_r=100):
    """the point on the stand's back edge at northing y and its outward normal (the edge of B, a densified outline,
    that crosses y on the side away from the pitch)"""
    best = None
    for i in range(len(B) - 1):
        p0, p1 = B[i], B[i + 1]
        if not (min(p0[1], p1[1]) <= y <= max(p0[1], p1[1])) or abs(p1[1] - p0[1]) < 1e-9: continue
        q = p0 + (p1 - p0) * (y - p0[1]) / (p1[1] - p0[1])
        if np.linalg.norm(q - PC) < min_r: continue
        if best is None or np.linalg.norm(q - PC) > np.linalg.norm(best[0] - PC):
            e = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([e[1], -e[0]]); n = n if n @ (q - PC) > 0 else -n
            best = (q, n)
    return best


def solid(m, Q, z0, z1, col, kind, top=None, bottom=False):
    """a vertical prism over the plan quad Q (4 points, either winding) from z0 to z1, with its top (and bottom)"""
    for k in range(4):
        a, b = Q[k], Q[(k + 1) % 4]; L = float(np.linalg.norm(b - a))
        m.add([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [(0, 1, 2, 3), (3, 2, 1, 0)],
              [col] * 4, [(0, z0), (L, z0), (L, z1), (0, z1)], kind)
    for z, on in ((z1, True), (z0, bottom)):
        if on: m.add([(q[0], q[1], z) for q in Q], [(0, 1, 2, 3), (3, 2, 1, 0)], [top or col] * 4,
                     [(float(q[0]), float(q[1])) for q in Q], 'concrete' if top else kind)


def entrance(m, B, st):
    """the main entrance between the brick towers (Google Earth from War Memorial Drive; the director's close-up of
    2026-11-22): a glazed ground floor standing out from the facade, its roof a terrace inside an orange-brick rim, three
    pale tensile canopies leaning back from the rim to the facade, and a dark round-topped pod at each end"""
    en = st['south_block']['entrance']; y0, y1 = en['y']; out = en['out']; H = en['h']
    f0, n0 = facade_at(B, st, y0); f1, n1 = facade_at(B, st, y1)
    t = (f1 - f0) / np.linalg.norm(f1 - f0); n = (n0 + n1) / np.linalg.norm(n0 + n1); W = float(np.linalg.norm(f1 - f0))
    # the facade steps (it stands 2 m further out between y -45 and -13): v counts from its outermost face
    vm = max(float((facade_at(B, st, y)[0] - f0) @ n) for y in np.linspace(y0, y1, 40))
    P = lambda u, v: f0 + t * u + n * (v + vm)   # u along the facade from y0, v out from it
    # the glazed ground floor: glass front and ends, a dark slab edge, the terrace deck on top
    bk = -vm - 0.3   # the back of the podium, inside the facade all along
    solid(m, [P(0, bk), P(W, bk), P(W, out), P(0, out)], 0.0, H - 0.6, en['glass'], 'glass')
    solid(m, [P(0, bk), P(W, bk), P(W, out + 0.15), P(0, out + 0.15)], H - 0.6, H, en['slab'], 'concrete', top=en['deck'])
    # the brick rim: a 1.1 m parapet round the terrace's front and ends, 0.45 m thick, coping on top
    r = 0.45; hr = en['rim_h']
    for Q in ([P(0, out - r), P(W, out - r), P(W, out + 0.15), P(0, out + 0.15)],
              [P(0, bk), P(r, bk), P(r, out - r), P(0, out - r)],
              [P(W - r, bk), P(W, bk), P(W, out - r), P(W - r, out - r)]):
        solid(m, Q, H - 1.6, H + hr, en['brick'], 'brick', top=en['coping'])
    # canopies: pale membranes, each pinned low at the rim and high at the facade, bellied down between
    cw, gap = en['canopy_w'], en['canopy_gap']; nC = len(en['canopy_u'])
    for uc in en['canopy_u']:
        nu, nv = 8, 6; V = []; UV = []
        for j in range(nv + 1):
            fv = j / nv; v = (out - 0.8) * (1 - fv) + 0.5 * fv; z = (H + en['canopy_z'][0]) * (1 - fv) + en['canopy_z'][1] * fv
            for i in range(nu + 1):
                fu = i / nu; u = uc - cw / 2 + cw * fu
                sag = en['sag'] * math.sin(math.pi * fu) * math.sin(math.pi * fv)
                p = P(u, v); V.append((p[0], p[1], z - sag)); UV.append((cw * fu, fv * 4))
        F = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i) for j in range(nv) for i in range(nu)]
        m.add(V, [f[::-1] for f in F], [en['canopy']] * len(V), UV, 'plain')   # one face, up: two coincident faces fought
        for u, v, zt in ((uc - cw / 2, out - 0.8, H + en['canopy_z'][0]), (uc + cw / 2, out - 0.8, H + en['canopy_z'][0])):
            p = P(u, v); box(m, (p[0], p[1], H), (p[0], p[1], zt), 0.18, en['post'], 'steel')   # masts at the low corners
        for u in (uc - cw / 2, uc + cw / 2):  # high corners tied back to the facade
            a, b = P(u, 0.5), P(u, 0.0); box(m, (a[0], a[1], en['canopy_z'][1]), (b[0], b[1], en['canopy_z'][1] + 0.3), 0.12, en['post'], 'steel')
    # pods: dark round-topped boxes standing on the terrace at each end
    for uc in en['pod_u']:
        w, d, h = en['pod']; rr = d / 2; vc = out - 0.8 - rr - 0.3
        prof = [(-rr, 0.0)] + [(rr * math.cos(a), h - rr + rr * math.sin(a)) for a in np.linspace(math.pi, 0, 9)] + [(rr, 0.0)]
        prof = prof[:1] + prof[1:-1] + prof[-1:]
        k = len(prof); V = []
        for side in (-w / 2, w / 2):
            for v, z in prof:
                p = P(uc + side, vc + v); V.append((p[0], p[1], H + z))
        F = [(j, j + 1, k + j + 1, k + j) for j in range(k - 1)]
        F += [(0, j, j + 1) for j in range(1, k - 1)] + [(k, k + j + 1, k + j) for j in range(1, k - 1)]
        m.add(V, F + [f[::-1] for f in F], [en['pod_col']] * len(V), [(v, z) for v, z in prof] * 2, 'steel')
    # the glass band's graphic (Google Earth shows pale shapes behind the glass, too blurred to read: not invented)


def green_wall(m, B, st, gw):
    """a planted wall: a stair core standing out of the facade beside a brick tower (Google Earth from War Memorial
    Drive: green from the ground most of the way up), its faces covered in climbing plants (the ivy part)"""
    global IVY
    if IVY is None: IVY = Mesh()
    (f0, n0), (f1, n1) = facade_at(B, st, gw['y'][0]), facade_at(B, st, gw['y'][1])
    n = (n0 + n1) / np.linalg.norm(n0 + n1); o = gw['out']
    Q = [f0 - n * 0.5, f1 - n * 0.5, f1 + n * o, f0 + n * o]
    solid(m, Q, 0.0, gw['h'], gw['col'], 'concrete', top=gw['col'])
    # leaves on the three outer faces, 0.15 m proud, up to a ragged top below the core's top
    rng = np.random.default_rng(int(abs(gw['y'][0]) * 10))
    for a, b in ((Q[3], Q[0]), (Q[2], Q[3]), (Q[1], Q[2])):
        e = b - a; L = float(np.linalg.norm(e)); nn = np.array([e[1], -e[0]]) / L
        if nn @ ((a + b) / 2 - (Q[0] + Q[2]) / 2) < 0: nn = -nn
        k = max(2, int(L / 0.6)); us = np.linspace(0, 1, k + 1); tops = gw['green'] + rng.uniform(-gw['rag'], gw['rag'], k + 1)
        for j in range(k):
            pa, pb = a + e * us[j] + nn * 0.15, a + e * us[j + 1] + nn * 0.15
            IVY.add([(pa[0], pa[1], 0.3), (pb[0], pb[1], 0.3), (pb[0], pb[1], tops[j + 1]), (pa[0], pa[1], tops[j])],
                    [(0, 1, 2, 3), (3, 2, 1, 0)], [gw['ivy']] * 4, [(L * us[j], 0.3), (L * us[j + 1], 0.3), (L * us[j + 1], tops[j + 1]), (L * us[j], tops[j])], 'grass')


# real seats (gate 2026-11-20, director: seats only): every seat its own moulded shell (pan and back) with a gap to the
# next, in rows on stepped concrete treads, in each stand's band colours; aisles every 14 m as on the old painted rows
ROW, PITCH_S, SEAT_W = 0.8, 0.5, 0.44
# shell profile across the row, (metres out from the row's front edge, metres above its tread): pan lip, pan, back
SHELL = [(0.30, 0.34), (0.32, 0.43), (0.66, 0.40), (0.72, 0.56), (0.78, 0.84)]
TREAD = (122, 120, 115)

SEAT_INST = []
SEAT_DROPPED = [0]
ROOF_GUARD = []   # (outline polygon, roof height function) for every roof, filled by the roof loop before any seat is placed
SEAT_HEAD = 2.6   # metres from a row's tread to the roof's underside: less and nobody could sit there (director 2026-11-21)

def seat_ok(q, z0, z1):
    """a seat is real only on a raked row (a flat deck is a concourse, not seating), and only where a person fits: under a
    roof with SEAT_HEAD of headroom, or in the open pitch-side of every roof. A seat behind a roof (the roof between it and
    the pitch) is outside the bowl"""
    from shapely.geometry import Point, LineString
    if z1 - z0 < 0.08: return False
    pt = Point(q[0], q[1]); ray = None
    for poly, rz, hang in ROOF_GUARD:
        if poly.contains(pt):
            under = rz(np.array([q]))[0] - 0.3
            if hang and poly.exterior.distance(pt) < hang[0]: under = under + 0.3 - hang[1]
            if under - z1 < SEAT_HEAD: return False
        else:
            ray = ray or LineString([tuple(q), tuple(PC)])
            if poly.intersects(ray): return False
    return True
def seat_shell():
    """one closed moulded seat (pan and back with 25 mm thickness) in seat-local metres: x across, y away from the pitch, z up;
    closed so it reads as a solid seat from below and from behind as well as from the front"""
    T = []
    for j, (dn, dz) in enumerate(SHELL):
        row = []
        for sx in (-1, -0.6, 0, 0.6, 1):              # five across: the back's sides wrap forward, top corners rounded
            wing = (0.07 if abs(sx) == 1 else 0.02 if sx else 0.0) if j >= 4 else (0.02 if abs(sx) == 1 else 0.0)
            drop = 0.07 if (abs(sx) == 1 and j == len(SHELL) - 1) else 0.0
            row.append((sx * SEAT_W / 2, dn - wing, dz - drop))
        T.append(row)
    T = np.array(T, float); nj = len(SHELL)
    N = np.zeros((nj, 2))                              # profile normals (y, z), facing up / toward the pitch
    for j in range(nj):
        a, b = SHELL[max(0, j - 1)], SHELL[min(nj - 1, j + 1)]; ty, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(ty, tz)
        N[j] = (-tz / L, ty / L)
    B = T.copy(); B[:, :, 1] -= N[:, None, 0] * 0.025; B[:, :, 2] -= N[:, None, 1] * 0.025
    V = np.r_[T.reshape(-1, 3), B.reshape(-1, 3)]; o = nj * 5; ix = lambda j, c: j * 5 + c
    F = [(ix(j, c), ix(j, c + 1), ix(j + 1, c + 1), ix(j + 1, c)) for j in range(nj - 1) for c in range(4)]
    F += [(o + ix(j, c), o + ix(j + 1, c), o + ix(j + 1, c + 1), o + ix(j, c + 1)) for j in range(nj - 1) for c in range(4)]
    for c in range(4):                                  # front lip and top edge
        F += [(ix(0, c + 1), ix(0, c), o + ix(0, c), o + ix(0, c + 1)), (ix(nj - 1, c), ix(nj - 1, c + 1), o + ix(nj - 1, c + 1), o + ix(nj - 1, c))]
    for j in range(nj - 1):                             # the two sides
        F += [(ix(j, 0), ix(j + 1, 0), o + ix(j + 1, 0), o + ix(j, 0)), (ix(j + 1, 4), ix(j, 4), o + ix(j, 4), o + ix(j + 1, 4))]
    UV = [(v[0], v[1] + v[2]) for v in V]
    return V, F, UV

def seat_rows(m, P, zfn, bands):
    """rows along lines at fixed distances from the pitch (the stand's rake), clipped to the outline P"""
    from shapely.geometry import Polygon, LineString
    inner = (P if hasattr(P, 'geom_type') else Polygon(P)).buffer(-0.3); pitch = Polygon(PITCH)
    lo = 0.0; ivs = []
    for b in bands:
        if (b[2] if len(b) > 2 else 'seats') == 'seats': ivs.append((lo, b[0], b[1]))
        lo = b[0]
    for d0, d1, col in ivs:
        dk = d0
        while dk + ROW <= d1 + 1e-6:
            ring = pitch.buffer(dk, 64).exterior; part = ring.intersection(inner)
            lines = getattr(part, 'geoms', [part])
            for ln in lines:
                if ln.geom_type != 'LineString' or ln.length < 1.0: continue
                def frame(s0):
                    q = np.array(ln.interpolate(s0).coords[0]); qa = np.array(ln.interpolate(max(0, s0 - 0.05)).coords[0]); qb = np.array(ln.interpolate(min(ln.length, s0 + 0.05)).coords[0])
                    t = qb - qa; t /= np.linalg.norm(t); nv = np.array([t[1], -t[0]])
                    if seg_dist((q + nv * 0.3)[None], PITCH)[0] < seg_dist((q - nv * 0.3)[None], PITCH)[0]: nv = -nv
                    zz = zfn(np.array([q, q + nv * ROW])); return q, t, nv, zz[0], max(zz[1], zz[0])
                # seats in blocks between aisles; each block starts at its aisle edge so the aisles run straight up the rake
                ss = np.arange(0, ln.length, 0.05); Q = np.array([ln.interpolate(x).coords[0] for x in ss])
                w = np.unwrap(np.arctan2(Q[:, 1] - PC[1], Q[:, 0] - PC[0])) * 90.0
                free = (w % 14.0) >= 1.2
                if BOX_KEEP_OUT:   # a media box splits the row like an aisle: the blocks beside it keep their seats
                    from shapely.geometry import MultiPolygon as _MP
                    from shapely import contains_xy
                    bx = _MP(BOX_KEEP_OUT).buffer(0.25); free &= ~contains_xy(bx, Q[:, 0], Q[:, 1])
                runs = []; st0 = None
                for x, f in zip(ss, free):
                    if f and st0 is None: st0 = x
                    if not f and st0 is not None: runs.append((st0, x)); st0 = None
                if st0 is not None: runs.append((st0, ln.length))
                for ra, rb in runs:
                    k = int((rb - ra) // PITCH_S)
                    if k < 1: continue
                    blk = []
                    for i in range(k):
                        s0 = ra + (rb - ra - k * PITCH_S) / 2 + (i + 0.5) * PITCH_S
                        q, t, nv, z0, z1 = frame(s0)
                        blk.append((q, nv, z0, z1))
                    # a block-row is seated only if every seat in it is real (seat_ok): raked, under the roof with
                    # headroom or in the open in front of it, never behind a roof. Otherwise the whole block-row goes,
                    # so a tier ends in a clean step at an aisle, not a ragged edge
                    if not all(seat_ok(q, z0, z1) for q, nv, z0, z1 in blk): SEAT_DROPPED[0] += k; continue
                    for q, nv, z0, z1 in blk:  # instanced: one seat shell placed at q, z1, local +y along nv (away from the pitch)
                        SEAT_INST.append((q[0], q[1], z1, math.atan2(-nv[0], nv[1]), *col))
                    # riser and tread under this block and half of each aisle beside it
                    a_, b_ = max(0.0, ra - 0.7), min(ln.length, rb + 0.7); n = max(1, int((b_ - a_) // PITCH_S))
                    V = []; UV = []
                    for x in np.linspace(a_, b_, n + 1):
                        q, t, nv, z0, z1 = frame(x); c = q + nv * ROW
                        V += [(q[0], q[1], z0), (q[0], q[1], z1), (c[0], c[1], z1)]; UV += [(x, z0), (x, z1), (x, z1 + ROW)]
                    F = [f for i in range(n) for f in ((3 * i, 3 * i + 3, 3 * i + 4, 3 * i + 1), (3 * i + 1, 3 * i + 4, 3 * i + 5, 3 * i + 2))]
                    m.add(V, F, [TREAD] * len(V), UV, 'concrete')
            dk += ROW

# ---------------------------------------------------------------- tier fronts (2026 photos: chappell, edwinsmith, bradman,
# riverbank, wanganeen_oatey, west_stands_2023). Each stand's pitch-facing storeys are built as solid parts along the lines
# at fixed distances from the pitch: brick walls, glazed levels with columns, fascias with the stand's name in raised
# letters, balcony slabs, the Bradman Pavilion's cream facade with real window openings. Nothing is painted on.
def _rel(a, c): return (a - c + 180.0) % 360.0 - 180.0

def in_sweep(ang, rng):
    """angles (deg) inside the sweep rng = [a0, a1] (deg, a0 < a1, may cross 0)"""
    c = (rng[0] + rng[1]) / 2; return np.abs(_rel(ang, c)) <= (rng[1] - rng[0]) / 2

def pt_ang(V): return np.degrees(np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0])) % 360.0

class Run:
    """a line at distance d from the pitch, clockwise round the ground (so +s reads left to right for someone on the
    ground facing the stand); at(s) -> point, outward normal (away from the pitch), tangent"""
    def __init__(s, Q):
        s.Q = Q; s.L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        s.A = np.unwrap(np.radians(pt_ang(Q)))
    def at(s, sv):
        sv = np.atleast_1d(np.asarray(sv, float)); q = np.c_[np.interp(sv, s.L, s.Q[:, 0]), np.interp(sv, s.L, s.Q[:, 1])]
        e = 0.05; qa = np.c_[np.interp(sv - e, s.L, s.Q[:, 0]), np.interp(sv - e, s.L, s.Q[:, 1])]
        qb = np.c_[np.interp(sv + e, s.L, s.Q[:, 0]), np.interp(sv + e, s.L, s.Q[:, 1])]
        t = qb - qa; t /= np.linalg.norm(t, axis=1)[:, None] + 1e-12
        n = q - PC; n /= np.linalg.norm(n, axis=1)[:, None]
        n = n - t * (n * t).sum(1)[:, None]; n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        return q, n, t
    def s_of(s, ang):
        """arc length where the line passes the angle ang (deg from the pitch centre)"""
        A = np.degrees(s.A); a = A[0] + _rel(ang, A[0] % 360.0)
        if not (min(A[0], A[-1]) <= a <= max(A[0], A[-1])): return None   # this run does not pass that angle
        return float(np.interp(a, A[::-1], s.L[::-1])) if A[-1] < A[0] else float(np.interp(a, A, s.L))

def runs_at(G_, d, rng=None, step=0.5):
    """the runs of the line at distance d inside geometry G_ (shapely), optionally only within the sweep rng"""
    from shapely.geometry import Polygon
    from shapely.ops import linemerge
    part = Polygon(PITCH).buffer(d, 256).exterior.intersection(G_)
    if part.geom_type == 'MultiLineString': part = linemerge(part)
    out = []
    for ln in getattr(part, 'geoms', [part]):
        if ln.geom_type != 'LineString' or ln.length < 1.0: continue
        n = max(2, int(ln.length / step)); Q = np.array([ln.interpolate(x).coords[0] for x in np.linspace(0, ln.length, n + 1)])
        a = np.unwrap(np.radians(pt_ang(Q)))
        if a[-1] > a[0]: Q = Q[::-1]
        if rng is not None:
            k = in_sweep(pt_ang(Q), rng); i = 0
            while i < len(Q):
                if not k[i]: i += 1; continue
                j = i
                while j < len(Q) and k[j]: j += 1
                if j - i > 2: out.append(Run(Q[i:j]))
                i = j
        else: out.append(Run(Q))
    return out

def quad(m, p, want, col, kind, uv=None):
    """one quad, wound so its front faces the direction `want`"""
    p = [np.asarray(x, float) for x in p]; nrm = np.cross(p[1] - p[0], p[3] - p[0])
    if nrm @ np.asarray(want, float) < 0: p = p[::-1]; uv = uv[::-1] if uv else uv
    m.add(p, [(0, 1, 2, 3)], [col] * 4, uv or [(0, 0), (1, 0), (1, 1), (0, 1)], kind)

def prism(m, run, s0, s1, e0, e1, z0, z1, col, kind, faces='fbtuel', step=1.0, top_col=None):
    """a solid along the run from s0 to s1: e0..e1 metres out from the line (e0 nearer the pitch), z0..z1 high"""
    n = max(1, int(math.ceil((s1 - s0) / step))); S_ = np.linspace(s0, s1, n + 1); q, nv, t = run.at(S_)
    P3 = lambda i, e, z: (q[i, 0] + nv[i, 0] * e, q[i, 1] + nv[i, 1] * e, z)
    for i in range(n):
        a, b = S_[i], S_[i + 1]; N0 = np.r_[-(nv[i] + nv[i + 1]) / 2, 0]
        if 'f' in faces: quad(m, [P3(i, e0, z0), P3(i + 1, e0, z0), P3(i + 1, e0, z1), P3(i, e0, z1)], N0, col, kind, [(a, z0), (b, z0), (b, z1), (a, z1)])
        if 'b' in faces: quad(m, [P3(i, e1, z0), P3(i + 1, e1, z0), P3(i + 1, e1, z1), P3(i, e1, z1)], -N0, col, kind, [(a, z0), (b, z0), (b, z1), (a, z1)])
        if 't' in faces: quad(m, [P3(i, e0, z1), P3(i + 1, e0, z1), P3(i + 1, e1, z1), P3(i, e1, z1)], (0, 0, 1), top_col or col, kind, [(a, e0), (b, e0), (b, e1), (a, e1)])
        if 'u' in faces: quad(m, [P3(i, e0, z0), P3(i + 1, e0, z0), P3(i + 1, e1, z0), P3(i, e1, z0)], (0, 0, -1), col, kind, [(a, e0), (b, e0), (b, e1), (a, e1)])
    for i, sg in ((0, -1), (n, 1)):
        if ('e' if sg < 0 else 'l') in faces:
            quad(m, [P3(i, e0, z0), P3(i, e1, z0), P3(i, e1, z1), P3(i, e0, z1)], np.r_[t[i] * sg, 0], col, kind, [(e0, z0), (e1, z0), (e1, z1), (e0, z1)])

def _cyl(m, a, b, r, col, kind, n=12):
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); d /= L
    u = np.cross(d, [1.0, 0, 0]) if abs(d[0]) < 0.9 else np.cross(d, [0, 1.0, 0]); u /= np.linalg.norm(u); v = np.cross(d, u)
    V = []; UV = []
    for k in range(n + 1):
        th = 2 * math.pi * k / n; e = math.cos(th) * u + math.sin(th) * v; V += [a + r * e, b + r * e]; UV += [(r * th, 0), (r * th, L)]
    F = [(2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2) for k in range(n)]
    nrm = np.cross(V[1] - V[0], V[2] - V[0]); out = (V[0] + V[2]) / 2 - a; out -= d * (out @ d)
    if nrm @ out < 0: F = [f[::-1] for f in F]
    m.add(V, F, [col] * len(V), UV, kind)

def tracked(text, weight, track):
    """the word with extra space between letters (track: a fraction of the cap height), as the stand signs are set"""
    from shapely.affinity import translate
    from shapely.ops import unary_union
    from matplotlib.textpath import TextPath
    from letters import glyph_polys, FONTS
    ext = lambda s: TextPath((0, 0), s, size=10, prop=FONTS[weight]).get_extents().width
    bar = ext('||'); cap = 7.29; x = 0.0; parts = []   # DejaVu's cap height at size 10; advance = ink between two bars
    for ch in text:
        if ch.strip(): parts.append(translate(glyph_polys(ch, weight), x, 0))
        x += ext('|' + ch + '|') - bar + track * cap
    return unary_union(parts)

def raised_text(m, run, text, s_mid, width, z0, cap, e_front, depth, col, weight='bold', back=False, track=0.0):
    """the word as solid letters: faces toward the pitch at e_front, `depth` thick, sides on every outline edge"""
    import shapely
    from letters import glyph_polys
    g = tracked(text, weight, track) if track else glyph_polys(text, weight)
    x0, y0, x1, y1 = g.bounds; sz = cap / (y1 - y0); sx = width / (x1 - x0)
    def P3(X, Y, e):
        s = s_mid - width / 2 + (X - x0) * sx; q, nv, _ = run.at(s); return (q[0, 0] + nv[0, 0] * e, q[0, 1] + nv[0, 1] * e, z0 + (Y - y0) * sz)
    eb = e_front + depth
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        for tri in shapely.constrained_delaunay_triangles(p).geoms:
            c = np.array(tri.exterior.coords)[:3]; F = [P3(x, y, e_front) for x, y in c]
            q, nv, _ = run.at(s_mid - width / 2 + (c[:, 0].mean() - x0) * sx); want = np.r_[-nv[0], 0]
            n0 = np.cross(np.subtract(F[1], F[0]), np.subtract(F[2], F[0]))
            if n0 @ want < 0: F = F[::-1]
            m.add(F, [(0, 1, 2)], [col] * 3, [(x, y) for x, y in c], 'plain')
            if back:
                B = [P3(x, y, eb) for x, y in c]
                if np.cross(np.subtract(B[1], B[0]), np.subtract(B[2], B[0])) @ want > 0: B = B[::-1]
                m.add(B, [(0, 1, 2)], [col] * 3, [(x, y) for x, y in c], 'plain')
        for ring in [p.exterior] + list(p.interiors):
            R = np.array(ring.coords)
            for k in range(len(R) - 1):
                (xa, ya), (xb, yb) = R[k], R[k + 1]; mx, my = (xa + xb) / 2, (ya + yb) / 2
                nx, ny = yb - ya, -(xb - xa); ln = math.hypot(nx, ny) + 1e-12; nx, ny = nx / ln, ny / ln
                if p.contains(shapely.geometry.Point(mx + nx * 1e-3, my + ny * 1e-3)): nx, ny = -nx, -ny   # outward in glyph space
                c0 = np.array(P3(mx, my, e_front)); c1 = np.array(P3(mx + nx * 0.5, my + ny * 0.5, e_front))
                quad(m, [P3(xa, ya, e_front), P3(xb, yb, e_front), P3(xb, yb, eb), P3(xa, ya, eb)], c1 - c0, col, 'plain',
                     [(0, 0), (1, 0), (1, depth), (0, depth)])

def window_facade(m, run, s0, s1, e, z0, z1, f, col, pane):
    """a rendered facade with real openings: piers and spandrels at e, panes set back f['recess'], reveals between,
    a timber door (fanlight above) at f['door'] degrees, sills and a cornice proud of the face"""
    bay, ww, wz0, wz1, rc = f['bay'], f['win'], f['wz'][0], f['wz'][1], f['recess']
    sd = run.s_of(f['door']) if f.get('door') is not None else None; dw = f.get('door_w', 1.6); dz1 = f.get('door_z', z0 + 2.9)
    n = max(1, int(round((s1 - s0) / bay))); bw = (s1 - s0) / n; ops = []
    for k in range(n):
        c = s0 + (k + 0.5) * bw
        if sd is not None and abs(c - sd) < bw / 2: ops.append((sd - dw / 2, sd + dw / 2, z0, dz1, 'door')); continue
        ops.append((c - ww / 2, c + ww / 2, wz0, wz1, 'win'))
    edges = [s0] + [x for o in ops for x in o[:2]] + [s1]
    for i in range(0, len(edges), 2):   # piers between openings, full height
        if edges[i + 1] - edges[i] > 0.01: prism(m, run, edges[i], edges[i + 1], e, e + 0.3, z0, z1, col, 'concrete', 'f')
    for a, b, oz0, oz1, kd in ops:
        if oz0 > z0: prism(m, run, a, b, e, e + 0.3, z0, oz0, col, 'concrete', 'f')     # below the sill
        prism(m, run, a, b, e, e + 0.3, oz1, z1, col, 'concrete', 'f')                     # above the head
        prism(m, run, a, b, e, e + rc, oz0, oz1, col, 'concrete', 'tu')                    # head and sill reveals
        prism(m, run, a, b, e, e + rc, oz0, oz1, col, 'concrete', 'el')                    # jambs
        if kd == 'door':
            prism(m, run, a, b, e + rc, e + rc + 0.05, oz0, oz1 - 0.7, f.get('door_col', (120, 64, 40)), 'timber', 'f')
            prism(m, run, a, b, e + rc, e + rc + 0.05, oz1 - 0.62, oz1, pane, 'glass', 'f')
            prism(m, run, a, b, e + rc - 0.04, e + rc, oz1 - 0.7, oz1 - 0.62, f.get('door_col', (120, 64, 40)), 'timber', 'ftu')
        else:
            prism(m, run, a, b, e + rc, e + rc + 0.05, oz0, oz1, pane, 'glass', 'f')
            prism(m, run, a - 0.1, b + 0.1, e - 0.08, e, oz0 - 0.12, oz0, f.get('sill', col), 'stone', 'ftuel')
    prism(m, run, s0, s1, e - f.get('cornice', 0.35), e, z1 - 0.35, z1, f.get('cornice_col', col), 'stone', 'ftuel')

def tier_parts(m, G_, parts, rng=None):
    """build each part along the line at its distance d, inside geometry G_ (and the sweep rng, if any)"""
    for pt in parts:
        prng = pt.get('ang', rng); t = pt['t']
        d0 = pt['d'][0] if isinstance(pt['d'], list) else pt['d']; d1 = pt['d'][1] if isinstance(pt['d'], list) else d0 + 0.05
        for run in runs_at(G_, d0, prng):
            L = run.L[-1]; e1 = d1 - d0
            if t == 'slab':
                prism(m, run, 0, L, 0, e1, pt['z'][0], pt['z'][1], pt['col'], pt.get('kind', 'concrete'), pt.get('faces', 'ftuel'), top_col=pt.get('top'))
            elif t == 'glass':
                prism(m, run, 0, L, 0, 0.05, pt['z'][0], pt['z'][1], pt['col'], 'glass', 'f')
                mc = pt.get('mull_col', (58, 60, 64))
                for s in np.arange(pt['mull'] / 2, L, pt['mull']): prism(m, run, s - 0.05, s + 0.05, -0.07, 0, pt['z'][0], pt['z'][1], mc, 'steel', 'fel')
                for z in pt.get('transoms', []): prism(m, run, 0, L, -0.06, 0, z - 0.04, z + 0.04, mc, 'steel', 'ftu')
            elif t == 'rail':   # glass balustrade with a steel top rail
                prism(m, run, 0, L, 0, 0.03, pt['z'][0], pt['z'][1] - 0.05, pt.get('col', (150, 170, 176)), 'glass', 'fb')
                prism(m, run, 0, L, -0.03, 0.06, pt['z'][1] - 0.05, pt['z'][1], (190, 192, 194), 'steel', 'ftu')
            elif t == 'cols':
                for s in np.arange(pt['every'] / 2 + pt.get('phase', 0.0), L - 0.3, pt['every']):
                    q, nv, _ = run.at(s); _cyl(m, (*q[0], pt['z'][0]), (*q[0], pt['z'][1]), pt['r'], pt['col'], 'concrete')
            elif t == 'facade':
                window_facade(m, run, 0, L, 0, pt['z'][0], pt['z'][1], pt, pt['col'], pt['pane'])
            elif t == 'clock':
                s = run.s_of(pt['at'])
                if s is None: continue
                q, nv, tg = run.at(s); c = np.r_[q[0], pt['z']]; n3 = np.r_[nv[0], 0]
                _cyl(m, c - n3 * 0.02, c - n3 * 0.14, pt['r'] + 0.06, (40, 42, 46), 'steel', 24)
                face = [c - n3 * 0.15 + pt['r'] * (math.cos(a) * np.r_[tg[0], 0] + math.sin(a) * np.r_[0, 0, 1]) for a in np.linspace(0, 2 * math.pi, 25)[:-1]]
                cc = c - n3 * 0.15; m.add([cc] + face, [(0, 1 + k, 1 + (k + 1) % 24) for k in range(24)] if np.cross(face[0] - cc, face[1] - cc) @ -n3 > 0 else
                                       [(0, 1 + (k + 1) % 24, 1 + k) for k in range(24)], [(244, 242, 236)] * 25, None, 'plain')
                for ang_, ln_ in ((math.radians(pt.get('h', 60)), 0.55), (math.radians(pt.get('mn', -30)), 0.8)):   # hands
                    tip = cc - n3 * 0.01 + pt['r'] * ln_ * (math.sin(ang_) * np.r_[tg[0], 0] + math.cos(ang_) * np.r_[0, 0, 1])
                    box(m, cc - n3 * 0.01, tip, 0.03, (30, 30, 32), 'steel')
            elif t == 'box':   # a camera or media box let into the upper tier's front rows (2026 photos): open to the
                # pitch, side walls and roof, glazed at the back; the seats it covers go to the seat check (headroom)
                if 'n' in pt:   # spread evenly along the tier (the Riverbank's, 2026 photo: one at every other aisle)
                    mg = pt.get('margin', 6.0); sl = [mg + (L - 2 * mg) * (i + 0.5) / pt['n'] for i in range(pt['n'])]
                else:
                    s0 = run.s_of(pt['at'])
                    if s0 is None: continue
                    sl = [s0 + off for off in pt['off']]
                for s in sl:
                    w = pt['w'] / 2
                    if not (0 < s - w and s + w < L): continue
                    zf, zr, tk = pt['z'][0], pt['z'][1], 0.25
                    for a_, b_ in ((s - w, s - w + tk), (s + w - tk, s + w)):   # side walls, down into the rake
                        prism(m, run, a_, b_, 0, e1, zf - 1.5, zr, pt['col'], 'concrete', 'fbtuel')
                    prism(m, run, s - w, s + w, -0.1, e1, zr, zr + 0.3, pt['col'], 'concrete', 'fbtuel')       # roof
                    prism(m, run, s - w, s + w, -0.12, 0.0, zr - 0.55, zr, pt.get('band', pt['col']), 'concrete', 'f')   # fascia
                    prism(m, run, s - w + tk, s + w - tk, e1 - 0.2, e1, zf - 1.5, zr, pt.get('back', (44, 48, 54)), 'concrete', 'f')
                    prism(m, run, s - w + tk, s + w - tk, e1 - 0.25, e1 - 0.2, zf + 1.0, zr - 0.3, pt.get('glass', (150, 176, 190)), 'glass', 'f')
                    prism(m, run, s - w + tk, s + w - tk, 0.0, 0.05, zf - 0.1, zf + 1.0, (150, 170, 176), 'glass', 'fb')  # front rail
                    from shapely.geometry import Polygon as _Pg
                    qq, nn, _ = run.at(np.array([s - w, s + w]))
                    BOX_KEEP_OUT.append(_Pg([qq[0] - nn[0] * 0.3, qq[1] - nn[1] * 0.3, qq[1] + nn[1] * e1, qq[0] + nn[0] * e1]))
            elif t == 'backwall':
                BACK_JOBS.append((run, pt))
            elif t == 'name':
                s = run.s_of(pt['at'])
                if s is not None and 0 < s - pt['w'] / 2 and s + pt['w'] / 2 < L:
                    raised_text(m, run, pt['text'], s, pt['w'], pt['z0'], pt['cap'], -pt.get('depth', 0.06), pt.get('depth', 0.06),
                                pt['col'], pt.get('weight', 'bold'), pt.get('back', False), pt.get('track', 0.0))
                    NAMES_DONE.append(pt['text'])

NAMES_DONE = []
BOX_KEEP_OUT = []   # floors of the media boxes: no seats there
def zone_wedge(rng):
    from shapely.geometry import Polygon
    A = np.radians(np.linspace(rng[0], rng[1], 60))
    return Polygon([tuple(PC)] + [tuple(PC + 500 * np.array([math.cos(a), math.sin(a)])) for a in A])
BACK_JOBS = []   # back walls that rise to the roof's underside: built once the roofs are known

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
def cut_low(P, le):
    """split a stand outline along the low_end line: (the full stand, the low seats beyond the line)"""
    from shapely.geometry import Polygon, LineString
    from shapely.ops import split
    a, b = np.array(le['line'], float); u = (b - a) / np.linalg.norm(b - a); n = np.array([-u[1], u[0]]) * le.get('side', 1)
    parts = split(Polygon(P).buffer(0), LineString([a - u * 500, b + u * 500])).geoms
    hi = [g for g in parts if (np.array(g.centroid.coords[0]) - a) @ n < 0]; lo = [g for g in parts if g not in hi]
    ring = lambda g: np.array(g.exterior.coords)
    return ring(max(hi, key=lambda g: g.area)), ring(max(lo, key=lambda g: g.area))

low_parts = []; seat_jobs = []
for st in S['stands']:
    P = stand_poly(st)
    if st.get('low_end'):  # the full stand ends in a wall on the line; low seats beyond it (c09 camera stands there)
        P, PL = cut_low(P, st['low_end']); low_parts.append((st, PL, st['low_end']))
        st = {k: v for k, v in st.items() if k != 'low_end'}
    ds = [k for k, _ in st['profile']] + [x for b in st['bands'] for x in (b[0] - 0.05, b[0] + 0.05)]
    for zn in st.get('zones', []): ds += [k for k, _ in zn['profile']] + [x for b in zn['bands'] for x in (b[0] - 0.05, b[0] + 0.05)]
    cr = iso_rings(P, sorted(set(ds)), st.get('step', 2.0))
    for zn in st.get('zones', []):   # the zone's side walls: two radial lines 8 cm apart at each end of its sweep
        rr = np.linalg.norm(P - PC, axis=1); rs = np.arange(rr.min() - 2, rr.max() + 2, 0.5)
        for a_ in zn['ang']:
            for da in (-0.04, 0.04):
                ang = math.radians(a_) + da / rs; cr = np.r_[cr, PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]]
    V, T = fill(P, st.get('step', 2.0), cr)
    d = seg_dist(V, PITCH)
    z = stand_z(st, V)
    C = band_colour(st['bands'], d); K = band_kind(st['bands'], d)
    for zn in st.get('zones', []):
        k = in_sweep(pt_ang(V), zn['ang'])
        if k.any():
            C[k] = band_colour(zn['bands'], d[k]); kz = band_kind(zn['bands'], d[k]); ki = np.nonzero(k)[0]
            for i, kk in zip(ki, kz): K[i] = kk
    # faces upward: Delaunay order is ccw in plan -> upward normal
    stands.add(np.c_[V, z], T, C, arc_uv(V, d), ['concrete' if k == 'seats' else k for k in K])  # under the stepped treads
    from shapely.geometry import Polygon as _Pg
    G_all = _Pg(P).buffer(0); G_base = G_all
    for zn in st.get('zones', []):
        W_ = zone_wedge(zn['ang']); G_z = G_all.intersection(W_); G_base = G_base.difference(W_)
        seat_jobs.append((G_z, lambda B, st=st: stand_z(st, B[:, :2]), zn['bands']))
        if zn.get('fronts'): tier_parts(stands, G_z, zn['fronts'])
    seat_jobs.append((G_base, lambda B, st=st: stand_z(st, B[:, :2]), st['bands']))
    if st.get('fronts'): tier_parts(stands, G_base, st['fronts'])
    zf = lambda B, st=st: stand_z(st, B[:, :2])
    parapet(stands, P, zf); front_skin(stands, P, zf)
    wb = st.get('wall_h')
    if wb:
        lift = None
        if st.get('arches'):   # the arcade builds the base wall's lower storey on its edges; the plain wall starts above it
            fl = not ccw(P)
            def lift(a, b, st=st, zf=zf, fl=fl):
                za, zb_ = np.minimum(zf(np.array([a, b])), wb)
                if arcade_edge(st, a, b, za, zb_, fl): return st['arches']['trim_z'][1]
                e = b - a; nrm = np.array([e[1], -e[0]]) * (-1 if fl else 1); mid = (a + b) / 2
                if nrm @ (mid - PC) > 0 and in_block(st, mid): return 99.0   # the south block's own storeys are its face:
                return None   # a brick wall here stood in front of its recessed glass floor (director's screenshot 2026-11-22)
        walls(stands, P, lambda B: np.minimum(zf(B), wb), 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'), lift=lift)
        if st.get('arches'): arcade(stands, P, zf, st)
        for bt in st.get('brick_towers', []): brick_tower(stands, P, bt, bt.get('col', st['wall']))   # the towers are a paler terracotta than the arcade (Google Earth)
        if st.get('south_block'): south_block(stands, P, st)
        for gw in st.get('green_walls', []):
            BB = densify(P, 2.0); green_wall(stands, np.r_[BB, BB[:1]], st, gw)
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
    elif st.get('wall_bands'):  # river (south gate photo): the outside wall in storeys, louvres and struts above
        for z0, z1, col, kind in st['wall_bands']:
            walls(stands, P, lambda B, z1=z1: np.minimum(zf(B), z1), z0, col, kind=kind, skip=st.get('wall_skip'))
        struts(stands, P, zf, st['struts'])
    else:
        walls(stands, P, zf, 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'), skip=st.get('wall_skip'))
for st, PL, le in low_parts:
    zl = lambda B, le=le: interp(le['profile'], seg_dist(B[:, :2], PITCH))
    V, T = fill(PL, 2.0, iso_rings(PL, [k for k, _ in le['profile']], 2.0)); d = seg_dist(V, PITCH)
    stands.add(np.c_[V, zl(V)], T, band_colour(st['bands'], d), arc_uv(V, d), ['concrete' if k == 'seats' else k for k in band_kind(st['bands'], d)])
    seat_jobs.append((PL, zl, st['bands']))
    walls(stands, PL, zl, 0.0, st['wall'], kind=st.get('wall_kind', 'concrete'))
stands.save('stands')
if IVY is not None: IVY.save('ivy')

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
        vv = rf['valleys']
        for i, f in enumerate(vv):  # the valley line, plus lines close beside it where the lobe rises steeply
            fs = [f]
            for k in rf.get('valley_rows', []):
                if i > 0: fs.append(f - k * (f - vv[i - 1]))
                if i < len(vv) - 1: fs.append(f + k * (vv[i + 1] - f))
            for g in fs:
                ang = rf['amid'] + a0 + g * (a1 - a0); r = np.arange(rlo, rhi, stp * 0.3)
                cr.append(PC + np.c_[np.cos(ang) * r, np.sin(ang) * r])
    vcr = list(cr)
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
        dfr_o = (bins, prof(cs <= -0.5, np.min, rf['d0']))  # the traced front's own distance per ray
        dfr = dfr_o if rf.get('front_fit') else None
    else: dfr = None
    if dbk is not None and rf.get('rebuild'):  # outline rebuilt from the smoothed edge distances: no traced wiggle
        from scipy.ndimage import gaussian_filter1d
        bb = dbk[0]; d1s = gaussian_filter1d(dbk[1], rf['rebuild'], mode='nearest')
        d0s = gaussian_filter1d(dfr_o[1], rf['rebuild'], mode='nearest')  # outline front: the traced front, smoothed
        dbk = (bb, d1s); dfr = (bb, d0s) if dfr is not None else None
        def rpt(a_rel, d):
            ang = a_rel + rf['amid']; Q = PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]
            return PC + np.array([np.cos(ang), np.sin(ang)]) * np.interp(d, np.maximum.accumulate(seg_dist(Q, PITCH)), rs)
        Fr = np.array([rpt(a, d) for a, d in zip(bb, d0s)]); Bk = np.array([rpt(a, d) for a, d in zip(bb, d1s)])
        P = np.r_[Fr, Bk[::-1], Fr[:1]]
    def roofz(V, rf=rf, a0=a0, a1=a1, dbk=dbk, dfr=dfr):
        d = seg_dist(V, PITCH)
        ang = (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
        d1 = np.interp(ang, *dbk) if dbk is not None else rf['d1']
        d0 = np.interp(ang, *dfr) if dfr is not None else rf['d0']
        t = np.clip((d - d0) / (d1 - d0), 0, 1)
        s = np.clip((ang - a0) / (a1 - a0), 0, 1)
        z = rf['hf'] + (rf['hb'] - rf['hf']) * interp(rf['tprof'], t)
        z = z - rf.get('dome', 0.0) * (2 * s - 1) ** 2
        if rf.get('hem_dz'):  # hem height read off the photo, per point along the stand (s 0..1), fading out to the back rim
            hd = np.array(rf['hem_dz'], float); z = z + np.interp(s, np.linspace(0, 1, len(hd)), hd) * (1 - t)
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
    if rf.get('front_cut'):  # front hem traced off the straight-down satellite (leaned frame): cut the outline there
        from shapely.geometry import Polygon
        la, lb = rf['front_cut']['lean']; F = np.array(rf['front_cut']['pts'], float); Fo = F.copy()
        for _ in range(3): F = Fo - np.c_[la * roofz(F), lb * roofz(F)]  # undo the lean: a point h m up shows (a*h, b*h) away
        u0 = F[0] - F[1]; u1 = F[-1] - F[-2]
        E = np.r_[[F[0] + u0 / np.linalg.norm(u0) * 60], F, [F[-1] + u1 / np.linalg.norm(u1) * 60]]
        far = PC + (E - PC) * 4.0
        keep = Polygon(np.r_[E, far[::-1]]).buffer(0); got = Polygon(P).buffer(0).intersection(keep)
        if got.geom_type != 'Polygon': got = max(got.geoms, key=lambda g: g.area)
        rr = rf['front_cut'].get('round', 0.0)  # metres: round the corners where the cut meets the end edges (no spike, no notch)
        if rr: got = got.buffer(-rr).buffer(rr).buffer(rr).buffer(-rr)
        if got.geom_type != 'Polygon': got = max(got.geoms, key=lambda g: g.area)
        P = np.array(got.exterior.coords)
        if rf['front_cut'].get('as_front'):  # depth runs from the hem itself, so the hem height is smooth along the stand
            Fd = densify(F, 0.5); Fa = (np.arctan2(Fd[:, 1] - PC[1], Fd[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
            o = np.argsort(Fa); dfr = (Fa[o], seg_dist(Fd, PITCH)[o])
            roofz = functools.partial(roofz, dfr=dfr)
    if dbk is not None:  # drop the fixed back-depth rings; put the rings on each ray's own back distance instead
        cr = list(vcr)  # keep the valley lines
        for ang in angs:
            Q = PC + np.c_[np.cos(ang) * rs, np.sin(ang) * rs]; dq = seg_dist(Q, PITCH)
            a_rel = (ang - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; d1 = np.interp(a_rel, *dbk)
            d0 = np.interp(a_rel, *dfr) if dfr is not None else rf['d0']
            for k in sorted(set(ks)):
                d = d0 + k * (d1 - d0)
                if dq.min() < d < dq.max(): cr.append(PC + np.array([[np.cos(ang), np.sin(ang)]]) * np.interp(d, dq, rs))
    V, T = fill(P, stp, np.concatenate(cr) if cr else None)
    z = roofz(V)
    uv = arc_uv(V, seg_dist(V, PITCH))
    m = Mesh(); m.add(np.c_[V, z], T, [rf['col']] * len(V), uv, 'roof')
    # second side (underside) so it shows from below: the membrane fabric itself, cream, lit through (photo west_stands_2023)
    m.add(np.c_[V, z - 0.3], [tuple(f[::-1]) for f in T], [rf['under']] * len(V), uv, 'roof')
    # back closure: on edges facing away from the pitch, a wall from the stand top (or ground) up to the roof edge
    if rf.get('back'):
        sp = {x.get('way'): x for x in S['stands']}[rf['stand']]; SP = stand_poly(sp); spath = Path(SP)
        B = densify(P, 1.5); B = np.r_[B, B[:1]]; zt = roofz(B[:, :2])
        inside = spath.contains_points(B)
        ztop = rf.get('back_z0', max(z for _, z in sp['profile']))   # the deck behind the top rows, where it is lower
        # where the roof's back edge overhangs the stand, the wall starts at the stand's top: the gap between the top
        # rows and the roof is closed from inside (back_west_2023: a white panel band under the roof's back edge)
        zb = np.where(inside, interp(sp['profile'], seg_dist(B, PITCH)), 0.0 if rf.get('back_ground', True) else ztop)
        zb = np.minimum(zb, zt - 0.3)
        for i in range(len(B) - 1):
            a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; nrm = np.array([e[1], -e[0]])
            if not ccw(P): nrm = -nrm  # outward side of the roof outline (right-hand normal of a ccw ring)
            if nrm @ (mid - PC) / (np.linalg.norm(nrm) * np.linalg.norm(mid - PC) + 1e-9) < 0.5: continue
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
        sp = {x.get('way'): x for x in S['stands']}[rf['stand']]
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
    from shapely.geometry import Polygon as _Poly
    eb = rf.get('eyebrow')  # the louvre and eyebrow band hang under the rim: no seat under them either
    ROOF_GUARD.append((_Poly(P).buffer(0), roofz, (eb['inset'] + 0.6, 0.3 + eb['tube'] + eb['glass'] + eb['band']) if eb else None))
    m.save('roof_' + rf['name'])

from shapely.geometry import Point
backs = Mesh()
for run, pt in BACK_JOBS:   # walls from a deck up to the roof's underside (the panelled wall behind a top row of seats)
    S_ = np.arange(0, run.L[-1] + 0.5, 1.0); S_[-1] = min(S_[-1], run.L[-1]); q, nv, _ = run.at(S_)
    top = []
    for x in q:
        zz = pt.get('z1', 30.0)
        for poly, rz, hang in ROOF_GUARD:
            if poly.contains(Point(x[0], x[1])): zz = min(zz, rz(np.array([x]))[0] - 0.35)
        top.append(zz)
    for i in range(len(S_) - 1):
        for e, sg in ((0.0, -1), (pt.get('thick', 0.3), 1)):
            p = [(*(q[i] + nv[i] * e), pt['z0']), (*(q[i + 1] + nv[i + 1] * e), pt['z0']), (*(q[i + 1] + nv[i + 1] * e), top[i + 1]), (*(q[i] + nv[i] * e), top[i])]
            quad(backs, p, np.r_[nv[i] * sg, 0], pt['col'], 'concrete', [(S_[i], pt['z0']), (S_[i + 1], pt['z0']), (S_[i + 1], top[i + 1]), (S_[i], top[i])])
if backs.f: backs.save('stands_back')
print('names built:', NAMES_DONE)
for i_, (P_, zfn_, bands_) in enumerate(seat_jobs):   # one file per stand (and the Hill's low seats), each well under 50 MB
    seats = Mesh(); n0 = len(SEAT_INST); seat_rows(seats, P_, zfn_, bands_)
    print('job', i_, 'faces', len(seats.f)); seats.save_bin('seats_%d' % i_) if seats.f else None; print('seats_%d' % i_, len(seats.f), 'tread faces', len(SEAT_INST) - n0, 'seats')
# the seats themselves: one shell, instanced (render.py: Geometry Nodes; game: MultiMesh), as on the MCG
os.makedirs(os.path.join(OUT, 'inst'), exist_ok=True)
_sv, _sf, _suv = seat_shell(); _sh = Mesh(); _sh.add(_sv, _sf, [(255, 255, 255)] * len(_sv), _suv, 'seats'); _sh.save('inst/seat_shell')
_I = np.array(SEAT_INST, np.float32)
np.savez_compressed(os.path.join(OUT, 'inst', 'seats.npz'), pos=_I[:, :3], yaw=_I[:, 3], col=_I[:, 4:7].astype(np.uint8))
print('seat instances', len(_I), 'block-row seats dropped by seat_ok', SEAT_DROPPED[0])

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
