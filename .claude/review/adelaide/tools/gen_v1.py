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

class Mesh:
    def __init__(s): s.v = []; s.c = []; s.f = []
    def add(s, V, F, C):
        o = len(s.v); s.v += [tuple(x) for x in V]; s.c += [tuple(x) for x in C]; s.f += [tuple(o + i for i in f) for f in F]
    def save(s, name):
        with open(os.path.join(OUT, name + '.ply'), 'w', newline='') as fh:
            fh.write('ply\nformat ascii 1.0\nelement vertex %d\nproperty float x\nproperty float y\nproperty float z\n'
                     'property uchar red\nproperty uchar green\nproperty uchar blue\nelement face %d\nproperty list uchar int vertex_indices\nend_header\n'
                     % (len(s.v), len(s.f)))
            for v, c in zip(s.v, s.c): fh.write('%.3f %.3f %.3f %d %d %d\n' % (*v, *[int(max(0, min(255, x))) for x in c]))
            for f in s.f: fh.write('%d %s\n' % (len(f), ' '.join(map(str, f))))

def interp(prof, d):
    prof = np.array(prof, float); return np.interp(d, prof[:, 0], prof[:, 1])

def band_colour(bands, d):
    out = np.zeros((len(d), 3))
    for i, x in enumerate(d):
        c = bands[-1][1]
        for lim, col in bands:
            if x <= lim: c = col; break
        out[i] = c
    return out

def ccw(P):
    a = 0.0
    for i in range(len(P) - 1): a += P[i, 0] * P[i + 1, 1] - P[i + 1, 0] * P[i, 1]
    return a > 0

def walls(m, P, ztop_fn, zbot, col, step=2.0):
    """vertical walls on every edge of P from zbot to ztop_fn(points), outward facing"""
    B = densify(P, step); B = np.r_[B, B[:1]]
    zt = ztop_fn(B); n = len(B)
    V = np.r_[np.c_[B, np.full(n, zbot)], np.c_[B, zt]]
    F = []
    flip = not ccw(P)
    for i in range(n - 1):
        q = (i, i + 1, n + i + 1, n + i)
        F.append(q[::-1] if flip else q)
    m.add(V, F, np.tile(col, (len(V), 1)))

# ---------------------------------------------------------------- build
ground = Mesh()
S = SPEC
gs = S['ground']
# lawn around the stadium
R0 = gs['size']
ground.add([(-R0, -R0, 0), (R0, -R0, 0), (R0, R0, 0), (-R0, R0, 0)], [(0, 1, 2, 3)], [gs['lawn']] * 4)
V, T = fill(PITCH, 4.0)
ground.add(np.c_[V, np.full(len(V), 0.05)], T, [gs['pitch']] * len(V))
ground.save('ground')

stands = Mesh()
for st in S['stands']:
    P = way(st['way'])
    V, T = fill(P, st.get('step', 2.0))
    d = seg_dist(V, PITCH)
    z = interp(st['profile'], d)
    C = band_colour(st['bands'], d)
    # faces upward: Delaunay order is ccw in plan -> upward normal
    stands.add(np.c_[V, z], T, C)
    zf = lambda B, st=st: interp(st['profile'], seg_dist(B[:, :2], PITCH))
    wb = st.get('wall_h')
    if wb:
        walls(stands, P, lambda B: np.minimum(zf(B), wb), 0.0, st['wall'])
        walls(stands, P, zf, wb, st['wall2'])
    else:
        walls(stands, P, zf, 0.0, st['wall'])
stands.save('stands')

for blk in S.get('blocks', []):
    m = Mesh(); P = way(blk['way']) if 'way' in blk else np.array(blk['poly'], float)
    if 'way' not in blk: P = np.r_[P, P[:1]]
    V, T = fill(P, 3.0)
    m.add(np.c_[V, np.full(len(V), blk['h'])], T, [blk['top']] * len(V))
    walls(m, P, lambda B, h=blk['h']: np.full(len(B), h), 0.0, blk['wall'])
    m.save('block_' + blk['name'])

# roofs: heightfield over the roof footprint, lobes along the stand
for rf in S['roofs']:
    P = way(rf['way']) + np.array(rf.get('off', [0, 0]), float)
    V, T = fill(P, rf.get('step', 1.5))
    a0, a1 = rf['a0'], rf['a1']
    if rf.get('off'):
        aa = (np.arctan2(P[:, 1] - PC[1], P[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; a0, a1 = aa.min(), aa.max()
    def roofz(V, rf=rf, a0=a0, a1=a1):
        d = seg_dist(V, PITCH)
        t = np.clip((d - rf['d0']) / (rf['d1'] - rf['d0']), 0, 1)
        ang = (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
        s = np.clip((ang - a0) / (a1 - a0), 0, 1)
        z = rf['hf'] + (rf['hb'] - rf['hf']) * interp(rf['tprof'], t)
        if rf.get('lobes'):
            if rf.get('valleys'):
                vv = np.array(rf['valleys']); i = np.clip(np.searchsorted(vv, s) - 1, 0, len(vv) - 2)
                fr = (s - vv[i]) / (vv[i + 1] - vv[i])
            else:
                k = rf['lobes']; fr = (s * k) % 1.0
            z = z + rf['lobeA'] * np.sqrt(np.clip(np.sin(math.pi * fr), 0, 1)) * interp(rf['lobet'], t)
        return z
    z = roofz(V)
    m = Mesh(); m.add(np.c_[V, z], T, [rf['col']] * len(V))
    # second side (underside) so it shows from below
    m.add(np.c_[V, z - 0.3], [tuple(f[::-1]) for f in T], [rf['under']] * len(V))
    # back closure: on edges facing away from the pitch, a wall from the stand top (or ground) up to the roof edge
    if rf.get('back'):
        sp = {x['way']: x for x in S['stands']}[rf['stand']]; SP = way(sp['way']); spath = Path(SP)
        B = densify(P, 1.5); B = np.r_[B, B[:1]]; zt = roofz(B[:, :2])
        zb = np.where(spath.contains_points(B), interp(sp['profile'], seg_dist(B, PITCH)), 0.0)
        zb = np.minimum(zb, zt - 0.3)
        for i in range(len(B) - 1):
            a, b = B[i], B[i + 1]; mid = (a + b) / 2; e = b - a; nrm = np.array([e[1], -e[0]])
            if nrm @ (mid - PC) < 0: nrm = -nrm
            if nrm @ (mid - PC) / (np.linalg.norm(nrm) * np.linalg.norm(mid - PC) + 1e-9) < 0.5: continue
            Vq = [(a[0], a[1], zb[i]), (b[0], b[1], zb[i + 1]), (b[0], b[1], zt[i + 1] - 0.2), (a[0], a[1], zt[i] - 0.2)]
            m.add(Vq, [(0, 1, 2, 3), (3, 2, 1, 0)], [rf['back']] * 4)
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
    tw.add(V, F, [TS['col']] * len(V))
    # head: a flat panel tilted toward the pitch
    dvec = PC - np.array([x, y]); dvec /= np.linalg.norm(dvec); side = np.array([-dvec[1], dvec[0]])
    hw, hh = TS['head_w'] / 2, TS['head_h']
    c0 = np.array([x, y]) + dvec * 0.8
    pts = []
    for sx in (-hw, hw):
        for zz in (H - hh, H + 0.5):
            lean = (zz - (H - hh)) * -0.25
            q = c0 + side * sx + dvec * lean; pts.append((q[0], q[1], zz))
    tw.add(pts, [(0, 2, 3, 1), (1, 3, 2, 0)], [TS['head']] * 4)
tw.save('towers')
print('ok', OUT)
