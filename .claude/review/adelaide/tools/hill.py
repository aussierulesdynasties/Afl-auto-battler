"""The Hill (north end) -> model/hill.ply.
Plan: OSM 191661675 (north seat terraces), 621872719 (heritage scoreboard) and the Esri 2025 mosaic read on labelled
metre grids (hill/plan_*.jpg): concourse, grass patches, paths, the big screen (shadow-fitted), the palisade fence.
Heights and looks: photos hill/cand/big_c00 (2026), c01 (2026), c09 (2022), c11 (2023) - see SOURCES.md.
Director 2026-11-19: "it is basically grass patches by the old historic scoreboard where people gather to watch".
The scoreboard's own painted lettering is on (director 2026-11-19: the ground's own signs yes, ads no); no sponsor
banner (the West End board on the palisade is left out), nothing on the screen, no trees."""
import json, os, math
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'model')
G = json.load(open(os.path.join(ROOT, 'osm/geo.json'), encoding='utf-8'))
KIND = {'plain': 0, 'seats': 1, 'concrete': 2, 'roof': 3, 'steel': 4, 'glass': 5, 'brick': 6, 'grass': 7, 'fins': 8,
        'timber': 9, 'copper': 10, 'stone': 11, 'turf': 12, 'board': 13, 'paving': 1}   # paving takes kind 1: the Hill's painted seat rows are gone (real seats), and the alpha byte holds kind*20 only up to 12

# material colours (daylight, read from the photos)
SEAT = (88, 112, 116); PAVE = (184, 180, 170); TURF = (96, 128, 58); DIRT = (128, 110, 82); RAIL = (170, 172, 172)
SB_BOARD = (30, 38, 34); SB_GREEN = (104, 132, 96); SB_CREAM = (222, 210, 168); SB_TOWER = (214, 204, 168)
WORN_TURF = (112, 120, 66)   # c00: the patch is worn grass, not a garden bed
SB_BRICK = (150, 78, 58); SB_ROOF = (118, 62, 50); BLACK = (24, 24, 26); STEEL = (70, 72, 74); SCREEN = (14, 16, 20)


class Mesh:
    def __init__(s): s.v = []; s.c = []; s.f = []; s.uv = []; s.k = []
    def add(s, V, F, C, UV, kind):
        o = len(s.v); s.v += [tuple(x) for x in V]; s.c += [tuple(x) for x in C]; s.uv += [tuple(x) for x in UV]
        s.k += [KIND[kind]] * len(V) if isinstance(kind, str) else [KIND[x] for x in kind]
        s.f += [tuple(o + i for i in f) for f in F]
    def quad(s, a, b, c, d, col, kind, uv=None):
        if uv is None:
            w = float(np.linalg.norm(np.subtract(b, a))); h = float(np.linalg.norm(np.subtract(d, a)))
            uv = [(0, 0), (w, 0), (w, h), (0, h)]
        s.add([a, b, c, d], [(0, 1, 2, 3)], [col] * 4, uv, kind)
    def save(s, name):
        hdr = ['ply', 'format ascii 1.0', 'element vertex %d' % len(s.v)] + ['property float ' + c for c in 'xyzst'] + \
              ['property uchar ' + c for c in ('red', 'green', 'blue', 'alpha')] + \
              ['element face %d' % len(s.f), 'property list uchar int vertex_indices', 'end_header']
        with open(os.path.join(OUT, name + '.ply'), 'w', newline='') as fh:
            fh.write('\n'.join(hdr) + '\n')
            for v, uv, c, k in zip(s.v, s.uv, s.c, s.k):
                fh.write('%.3f %.3f %.3f %.3f %.3f %d %d %d %d\n' % (*v, *uv, *[int(max(0, min(255, x))) for x in c], k * 20))
            for f in s.f: fh.write('%d %s\n' % (len(f), ' '.join(map(str, f))))


def densify(P, step):
    out = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]; n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(n): out.append(a + (b - a) * k / n)
    return np.array(out)


def seg_dist(Q, P, closed=False):
    """distance from points Q to polyline P"""
    A = P[:-1]; B = P[1:]; D = B - A
    t = np.clip(((Q[:, None, :] - A[None]) * D[None]).sum(-1) / (D * D).sum(-1)[None], 0, 1)
    C = A[None] + t[..., None] * D[None]
    return np.sqrt(((Q[:, None, :] - C) ** 2).sum(-1)).min(1)


def fill(P, step, extra=None):
    path = Path(P); B = densify(P, step)
    lo, hi = P.min(0), P.max(0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
    I = np.c_[gx.ravel(), gy.ravel()]; I = I[path.contains_points(I)]
    if len(I): I = I[seg_dist(I, P) > step * 0.4]
    if extra is not None:
        E = extra[path.contains_points(extra)]; E = E[seg_dist(E, P) > step * 0.3]
        from scipy.spatial import cKDTree
        if len(I) and len(E): I = I[cKDTree(E).query(I)[0] > step * 0.5]
        I = np.r_[I, E]
    V = np.r_[B, I]; T = Delaunay(V).simplices
    T = T[path.contains_points(V[T].mean(1))]
    # Delaunay order is ccw in plan -> upward normals
    return V, T


def box3(m, c, u, n, su, sn, z0, z1, col, kind, top=None, sides=(1, 1, 1, 1)):
    """axis box in the frame (u, n) centred on plan point c, size su x sn, from z0 to z1; walls + top"""
    c = np.asarray(c, float); u = np.asarray(u, float); n = np.asarray(n, float)
    P = [c - u * su / 2 - n * sn / 2, c + u * su / 2 - n * sn / 2, c + u * su / 2 + n * sn / 2, c - u * su / 2 + n * sn / 2]
    for i in range(4):
        if not sides[i]: continue
        a, b = P[i], P[(i + 1) % 4]
        m.quad((*a, z0), (*b, z0), (*b, z1), (*a, z1), col, kind)
    m.quad(*[(*p, z1) for p in P], top if top is not None else col, kind)


def beam(m, a, b, w, col, kind):
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); d /= L
    u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0])
    v = np.cross(u, d); h = w / 2; off = [(-h, -h), (h, -h), (h, h), (-h, h)]
    V = [a + x * u + y * v for x, y in off] + [b + x * u + y * v for x, y in off]
    F = [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
    m.add(V, F, [col] * 8, [(i * w, 0) for i in range(4)] + [(i * w, L) for i in range(4)], kind)


def strip_wall(m, L, zb, zt, col, kind, outward=None):
    """vertical wall along polyline L (n,2) from zb(points) to zt(points) (callables or numbers)"""
    zb_ = zb(L) if callable(zb) else np.full(len(L), zb); zt_ = zt(L) if callable(zt) else np.full(len(L), zt)
    n = len(L); V = np.r_[np.c_[L, zb_], np.c_[L, zt_]]
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(L, axis=0), axis=1))]
    F = [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)]
    F += [f[::-1] for f in F]   # two-sided (fences, thin walls)
    m.add(V, F, [col] * len(V), np.r_[np.c_[s, zb_], np.c_[s, zt_]], kind)


m = Mesh()
SW = np.array(G['ways']['191661675'], float)
# ---------------------------------------------------------------- north seat terraces (OSM 191661675)
# back edge (concourse side) and front edge (pitch side) of the OSM ring
BACK = np.array([(-65.3, 70.3), (-60.1, 77.5), (-54.7, 83.2), (-50.7, 86.8), (-43.0, 92.2), (-32.8, 97.2), (-25.0, 99.9),
                 (-10.7, 102.1), (-3.0, 101.6), (9.4, 100.1), (17.8, 97.5), (27.8, 92.3), (33.4, 91.3)])
FRONT = np.array([(23.3, 78.5), (20.8, 80.2), (17.9, 82.1), (13.7, 84.0), (9.6, 85.6), (4.2, 87.0), (-0.3, 88.0),
                  (-5.0, 88.2), (-10.2, 88.4), (-15.7, 88.1), (-21.3, 86.9), (-27.5, 85.0), (-32.5, 82.9), (-37.4, 79.9),
                  (-41.7, 76.9), (-46.0, 73.1), (-49.9, 68.9), (-53.1, 64.0)])
Z_FRONT, Z_BACK = 0.6, 3.2          # c11/c07: about 14 rows behind the fence, back at the concourse
def seat_z(V):
    df, db = seg_dist(V, densify(FRONT, 0.5)), seg_dist(V, densify(BACK, 0.5))
    return Z_FRONT + (Z_BACK - Z_FRONT) * df / np.maximum(df + db, 1e-6), df
P = np.r_[BACK, FRONT, BACK[:1]]
if np.sum(P[:-1, 0] * P[1:, 1] - P[1:, 0] * P[:-1, 1]) < 0: P = P[::-1]
V, T = fill(P, 1.0)
z, df = seat_z(V)
a = np.unwrap(np.arctan2(V[:, 1], V[:, 0])); r = np.linalg.norm(V, axis=1)
m.add(np.c_[V, z], T, [(122, 120, 115)] * len(V), np.c_[a * 95.0, df], 'concrete')   # under the stepped treads
# real seats (director 2026-11-21: "are these meant to be chairs?" - the painted rows are gone): rows every 0.8 m back
# from the front wall, each seat its own instanced shell on a stepped concrete tread, aisles every 12 m, as gen.py does
# for the stands. Seat colour: the sage green-grey of the photos (c07, c11)
from shapely.geometry import Polygon as _Poly, LineString as _LS
ROW, PITCH_S = 0.8, 0.5; HILL_SEATS = []; _ter = _Poly(P).buffer(-0.3); _fr = _LS(FRONT)
dk = 0.4
while dk < 16.0:
    ring = _fr.buffer(dk, 32); ln_all = ring.exterior.intersection(_ter)
    for ln in getattr(ln_all, 'geoms', [ln_all]):
        if ln.geom_type != 'LineString' or ln.length < 2.0: continue
        def frame(s0):
            q = np.array(ln.interpolate(s0).coords[0]); qa = np.array(ln.interpolate(max(0, s0 - 0.05)).coords[0])
            qb = np.array(ln.interpolate(min(ln.length, s0 + 0.05)).coords[0]); t = qb - qa; t /= np.linalg.norm(t)
            nv = np.array([t[1], -t[0]])
            if _fr.distance(_Point(*(q + nv * 0.3))) < _fr.distance(_Point(*(q - nv * 0.3))): nv = -nv
            zz = seat_z(np.array([q, q + nv * ROW]))[0]; return q, nv, zz[0], max(zz[1], zz[0])
        from shapely.geometry import Point as _Point
        # blocks between aisles 1.2 m wide every 12 m along the row
        L = ln.length; nb = max(1, int(round(L / 12.0))); edges = np.linspace(0, L, nb + 1)
        for i in range(nb):
            ra, rb = edges[i] + (0.6 if i > 0 else 0.2), edges[i + 1] - (0.6 if i < nb - 1 else 0.2)
            k = int((rb - ra) // PITCH_S)
            if k < 1: continue
            for j in range(k):
                q, nv, z0, z1 = frame(ra + (rb - ra - k * PITCH_S) / 2 + (j + 0.5) * PITCH_S)
                HILL_SEATS.append((q[0], q[1], z1, math.atan2(-nv[0], nv[1]), 95, 118, 112))
            a_, b_ = max(0.0, ra - 0.6), min(L, rb + 0.6); n = max(1, int((b_ - a_) // PITCH_S)); Vt = []; UVt = []
            for x in np.linspace(a_, b_, n + 1):
                q, nv, z0, z1 = frame(x); c = q + nv * ROW
                Vt += [(q[0], q[1], z0), (q[0], q[1], z1), (c[0], c[1], z1)]; UVt += [(x, z0), (x, z1), (x, z1 + ROW)]
            Ft = [f for i2 in range(n) for f in ((3 * i2, 3 * i2 + 3, 3 * i2 + 4, 3 * i2 + 1), (3 * i2 + 1, 3 * i2 + 4, 3 * i2 + 5, 3 * i2 + 2))]
            m.add(Vt, Ft, [(122, 120, 115)] * len(Vt), UVt, 'concrete')
    dk += ROW
_HS = np.array(HILL_SEATS, np.float32); os.makedirs(os.path.join(OUT, 'inst'), exist_ok=True)
np.savez_compressed(os.path.join(OUT, 'inst', 'seats_hill.npz'), pos=_HS[:, :3], yaw=_HS[:, 3], col=_HS[:, 4:7].astype(np.uint8))
print('hill seats', len(_HS))
# side ends of the terrace: concrete walls down to the ground
for a_, b_ in ((BACK[0], FRONT[-1]), (BACK[-1], FRONT[0])):
    L = densify(np.array([a_, b_, b_]), 0.5); L = np.r_[L, [b_]]
    strip_wall(m, L, 0.0, lambda Q: seat_z(Q)[0], PAVE, 'concrete')
# front wall below the first row
strip_wall(m, np.r_[densify(np.r_[FRONT, FRONT[-1:]], 1.0), FRONT[-1:]], 0.0, Z_FRONT, (60, 62, 64), 'concrete')
# steel rail along the back of the seats (c07, c09, c11), posts every 2.5 m
RB = densify(np.r_[BACK, BACK[-1:]], 2.5)
for i, p in enumerate(RB):
    beam(m, (*p, Z_BACK), (*p, Z_BACK + 1.0), 0.06, RAIL, 'steel')
    if i + 1 < len(RB): beam(m, (*p, Z_BACK + 1.0), (*RB[i + 1], Z_BACK + 1.0), 0.06, RAIL, 'steel')

# ---------------------------------------------------------------- the Hill: concourse, grass, paths (Esri 2025 plan)
SB = np.array(G['ways']['621872719'], float)[:4]           # (14.2,119.2) (19.7,128.0) (35.9,118.0) (30.4,109.2)
U = (SB[3] - SB[0]) / np.linalg.norm(SB[3] - SB[0])        # along the scoreboard face, west -> east
N = (SB[1] - SB[0]) / np.linalg.norm(SB[1] - SB[0])        # from the face to the back
# outer edge: the black palisade line behind the patches (c00, c01) from the west stand to the scoreboard, then the
# scoreboard's back, the amenities box and the east stand's north end
OUTER = np.array([(-78.6, 72.3), (-80.5, 77.0), (-77.0, 87.5), (-66.0, 99.0), (-55.0, 99.0), (-45.0, 98.5), (-35.0, 101.0),
                  (-26.0, 104.5), (-21.0, 111.0), (-19.5, 121.5), (8.0, 121.5), tuple(SB[0]), tuple(SB[1]), tuple(SB[2]),
                  (40.9, 111.1), (44.0, 106.0), (52.0, 95.0), (49.2, 83.2), (45.8, 86.1), (42.2, 88.8), (39.2, 90.6)])
HILL = np.r_[OUTER, BACK[::-1], OUTER[:1]]
if np.sum(HILL[:-1, 0] * HILL[1:, 1] - HILL[1:, 0] * HILL[:-1, 1]) < 0: HILL = HILL[::-1]
Z_TOP = 4.2                          # c09: the grass rises gently from the seat-back concourse to the scoreboard
def hill_z(Q):
    return np.minimum(Z_BACK + 0.06 * seg_dist(Q, densify(np.r_[BACK, BACK[-1:]], 0.5)), Z_TOP)
GRASS = [  # grass patches (Esri plan grid + photos c07, c09, c11)
    [(-75.0, 87.0), (-61.0, 80.5), (-57.5, 86.5), (-60.0, 96.0), (-66.0, 98.0), (-71.0, 93.0)],                # NW corner
    [(9.0, 106.5), (17.0, 103.0), (27.0, 97.5), (33.5, 95.5), (37.6, 101.0), (34.8, 104.7),
     (29.0, 107.6), (16.5, 115.5), (10.5, 118.0), (7.5, 113.0)],                                                              # by the scoreboard
]
WORN = [[(-19.5, 107.0), (4.0, 106.5), (1.5, 110.5), (-4.0, 117.0), (-12.5, 117.0), (-19.0, 112.0)]]           # worn patch, c00
PATHS = [[(0.5, 106.5), (5.5, 106.5), (13.0, 120.0), (8.0, 121.5)],                                          # path to the north gate
         [(-62.0, 98.0), (-59.0, 97.0), (-53.5, 91.0), (-55.0, 89.5)]]                                         # NW diagonal path
def zone(V):
    k = np.array(['paving'] * len(V), object); C = np.tile(PAVE, (len(V), 1)).astype(float)
    for polys, kk, col in ((GRASS, 'turf', TURF), (WORN, 'turf', WORN_TURF), (PATHS, 'paving', PAVE)):
        for poly in polys:
            q = Path(np.r_[poly, poly[:1]]).contains_points(V); k[q] = kk; C[q] = col
    dB = seg_dist(V, densify(np.r_[BACK, BACK[-1:]], 0.5))
    q = dB < 4.8; k[q] = 'paving'; C[q] = PAVE      # concourse behind the seat rail, about 5 m wide
    return list(k), C
extra = np.concatenate([densify(np.r_[p, p[:1]], 0.5) for p in GRASS + WORN + PATHS])
_bd = densify(np.r_[BACK, BACK[-1:]], 0.4); _bn = _bd / np.linalg.norm(_bd, axis=1)[:, None]   # concourse edge as a mesh line
extra = np.r_[extra, _bd + _bn * 4.8]
V, T = fill(HILL, 1.0, extra)
# concrete kerb round every grass patch (c07, c09: the patches are edged), 0.15 m up, 0.2 m wide
for poly in GRASS + WORN:
    Lk = densify(np.r_[poly, poly[:1]], 0.5); Lk = np.r_[Lk, Lk[:1]]
    strip_wall(m, Lk, lambda Q: hill_z(Q) - 0.05, lambda Q: hill_z(Q) + 0.15, (196, 192, 182), 'concrete')
k, C = zone(V)
# a triangle takes the zone of its centroid: split vertices so patch edges stay crisp
Vc = V[T].mean(1); kc, Cc = zone(Vc)
VV = V[T].reshape(-1, 2); zz = hill_z(VV)
m.add(np.c_[VV, zz], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(T))], np.repeat(Cc, 3, 0),
      VV, [x for x in kc for _ in range(3)])
# grass batter outside the palisade down to the parkland lawn (z 0), 5 m wide
FENCE = np.r_[densify(OUTER[:11], 0.5), OUTER[10:11]]
EDGE = np.r_[densify(OUTER[:19], 0.5), OUTER[18:19]]   # the whole outer edge (the fence line, the scoreboard's back, the east end): the Hill is a mound, grassed down to the parkland all round (director 2026-11-21: nothing floating)
def outward(L):
    d = np.gradient(L, axis=0); nrm = np.c_[d[:, 1], -d[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    mid = L + nrm; return nrm if np.mean(Path(HILL).contains_points(mid)) < 0.5 else -nrm
from scipy.ndimage import gaussian_filter1d as _g1
nb = outward(EDGE); nb = np.c_[_g1(nb[:, 0], 4, mode='nearest'), _g1(nb[:, 1], 4, mode='nearest')]
nb /= np.linalg.norm(nb, axis=1)[:, None]; Lo = EDGE + nb * 8.0; nL = len(EDGE)   # 8 m: a 1-in-2 grass bank
Vb = np.r_[np.c_[EDGE, hill_z(EDGE) - 0.02], np.c_[Lo, np.full(nL, -0.05)]]
Fb = [(i, nL + i, nL + i + 1, i + 1) for i in range(nL - 1)]
Fb += [f[::-1] for f in Fb]   # both faces: the bank must never read as a slab edge from any side
m.add(Vb, Fb, [TURF] * len(Vb), np.r_[EDGE, Lo], 'turf')
# black palisade fence, 1.8 m (c00, c01)
strip_wall(m, FENCE, hill_z, lambda Q: hill_z(Q) + 1.8, BLACK, 'fins')

# NW corner: covered viewing shelter (photo c07 is taken from under it) and the long white rail (Esri plan)
SH = [(-79.0, 79.4), (-66.3, 75.0), (-65.4, 77.6), (-78.1, 82.0)]
zsh = float(hill_z(np.array([(-72.0, 78.5)]))[0])
_Q = [(*p, zsh + 2.7) for p in SH] + [(*p, zsh + 2.95) for p in SH]   # a roof slab 0.25 m thick, not a sheet
_F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)]
m.add(_Q, _F + [f[::-1] for f in _F], [(64, 66, 68)] * 8, [(q[0], q[1]) for q in _Q], 'steel')
for p in (SH[2], SH[3], (np.add(SH[2], SH[3]) / 2)):
    beam(m, (*p, zsh), (*p, zsh + 2.7), 0.2, (64, 66, 68), 'steel')
RL = densify(np.array([(-74.6, 86.2), (-60.9, 80.6), (-60.9, 80.6)]), 2.0)
for i, p in enumerate(RL):
    zp = float(hill_z(p[None])[0]); beam(m, (*p, zp), (*p, zp + 1.0), 0.08, (226, 226, 222), 'steel')
    if i + 1 < len(RL): beam(m, (*p, zp + 1.0), (*RL[i + 1], float(hill_z(RL[i + 1][None])[0]) + 1.0), 0.1, (226, 226, 222), 'steel')
# ---------------------------------------------------------------- heritage scoreboard (OSM 621872719; c01, c09, c11)
# local frame: s along the face from the west corner (0..19.07), t from the front edge to the back (0..10.38)
LS, LT = np.linalg.norm(SB[3] - SB[0]), np.linalg.norm(SB[1] - SB[0])
def W(s, t, z): p = SB[0] + U * s + N * t; return (p[0], p[1], z)
zb = float(hill_z(np.array([SB[0] + U * LS / 2]))[0])   # base level (path in front)
S_TW = LS - 1.7                    # tower: east end, 1.7 m wide on the face, deep (c11 front, c01/c09 side)
S_BR = LS - 3.0                    # brick base 3 m wide under it (c11)
T_F = 2.0                          # board face set back 2 m behind the verandah front (c09)
T_B = 4.3                          # back of the board and tower: c09 tower side back-projected (t 4.1-4.5)
TTW = 1.5                          # tower front above the verandah: c09 shows the board numbers up to it and the side windows at t 1.5-2.7
TPAR = 2.1                         # board parapet front: c09 posts back-projected at t 2.0-2.5 (z matches c11)
TT = 0.7                           # tower-top parapet front: c09 tower posts at t 0.1-0.5, cornice 0.9 out from TTW
Z_VER, Z_CORN, Z_PAR, Z_PED, Z_VANE = zb + 3.2, zb + 11.6, zb + 12.95, zb + 14.92, zb + 17.0   # c11 at ~50 px/m
def wallq(s0, t0, s1, t1, z0, z1, col, kind):
    m.quad(W(s0, t0, z0), W(s1, t1, z0), W(s1, t1, z1), W(s0, t0, z1), col, kind)
# board: dark green face with panel joints, cream-painted back and ends
wallq(0, T_F, S_TW, T_F, Z_VER, Z_CORN, SB_BOARD, 'board')
# painted lettering (c11 face-on, traced on the board and back-projected through camH11b; tools/sbmap.py): word, s0, z0, s1, z1
# above the path. Hand-made: DejaVu Sans Bold outlines stretched to each traced box (tools/letters.py). Board yellow from c11.
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from letters import word_tris
SB_WORDS = [('V', 10.71, 11.02, 11.16, 11.56),('BOWLERS', 4.99, 10.15, 7.16, 10.85),('WKTS', 7.37, 10.2, 8.49, 10.87),('RUNS', 8.77, 10.22, 9.95, 10.87),('BATSMEN', 10.25, 10.27, 12.41, 10.91),('OUT', 12.73, 10.31, 13.62, 10.91),('B', 13.73, 10.31, 14.02, 10.91),('RUNS', 14.13, 10.32, 15.2, 10.92),('FALL', 15.4, 10.34, 16.16, 10.94),('OF', 16.19, 10.53, 16.48, 10.81),('WKTS', 16.5, 10.37, 17.54, 10.97),('1', 0.14, 10.18, 0.35, 10.74),('ST', 0.42, 10.46, 0.77, 10.73),('INNINGS', 0.95, 10.19, 2.6, 10.76),('2', 0.1, 9.6, 0.38, 10.12),('ND', 0.41, 9.84, 0.78, 10.11),('INNINGS', 0.95, 9.6, 2.6, 10.14),('1', 0.15, 8.35, 0.36, 8.88),('ST', 0.42, 8.6, 0.77, 8.87),('INNINGS', 0.95, 8.35, 2.6, 8.9),('2', 0.1, 7.75, 0.38, 8.27),('ND', 0.41, 7.99, 0.78, 8.25),('INNINGS', 0.96, 7.75, 2.6, 8.29),('WICKETS', 0.2, 6.93, 2.5, 7.5),('SUNDRIES', 0.11, 4.65, 2.52, 5.26),('TOTAL', 0.34, 3.91, 2.5, 4.5),('UMPIRES', 7.94, 3.44, 10.04, 3.99),('1', 4.67, 9.54, 4.85, 10.07),('2', 4.6, 8.92, 4.97, 9.45),('3', 4.6, 8.3, 4.98, 8.84),('4', 4.6, 7.7, 4.98, 8.24),('5', 4.59, 7.07, 4.97, 7.61),('6', 4.59, 6.44, 4.97, 7.0),('7', 4.59, 5.83, 4.97, 6.39),('8', 4.59, 5.22, 4.97, 5.77),('9', 4.59, 4.61, 4.97, 5.15),('1', 15.57, 9.74, 15.73, 10.19),('FOR', 15.78, 9.76, 16.23, 10.1),('2', 15.45, 9.1, 15.82, 9.63),('3', 15.46, 8.46, 15.82, 9.01),('4', 15.46, 7.85, 15.84, 8.39),('5', 15.45, 7.24, 15.84, 7.77),('6', 15.46, 6.6, 15.83, 7.14),('7', 15.46, 5.98, 15.83, 6.52),('8', 15.46, 5.33, 15.82, 5.89),('9', 15.45, 4.73, 15.81, 5.28),('OVERS', 15.12, 4.33, 16.15, 4.71),("R'QD", 15.25, 3.87, 16.07, 4.25)]
SB_YEL = (206, 160, 44)
for w, s0, z0, s1, z1 in SB_WORDS:
    s0, s1 = [(s + 0.11) / 17.68 * S_TW for s in (s0, s1)]          # c11 board edges s -0.11..17.57 -> the model board 0..S_TW
    V2, T2 = word_tris(w, (s0, z0, s1, z1))
    m.add([W(a, T_F - 0.03, zb + b) for a, b in V2], [tuple(x) for x in T2] + [tuple(x[::-1]) for x in T2], [SB_YEL] * len(V2), [tuple(v) for v in V2], 'plain')
# the small paired dots in c11: after the right-hand numbers 2-9 and under each ND
def sb_dot(s, z, d=0.075):
    s = (s + 0.11) / 17.68 * S_TW
    m.quad(W(s, T_F - 0.03, zb + z), W(s + d, T_F - 0.03, zb + z), W(s + d, T_F - 0.03, zb + z + d), W(s, T_F - 0.03, zb + z + d), SB_YEL, 'plain')
for w, s0, z0, s1, z1 in SB_WORDS:
    if s0 > 15.4 and w in '23456789':
        zm = (z0 + z1) / 2 - 0.04
        sb_dot(s1 + 0.06, zm); sb_dot(s1 + 0.2, zm)
    if w == 'ND':
        sb_dot(s0 + 0.08, z0 - 0.14); sb_dot(s0 + 0.22, z0 - 0.14)
wallq(S_TW, T_B, 0, T_B, zb, Z_CORN, SB_TOWER, 'timber')
# the back (what the Hill sees): cream weatherboard in bays between green pilasters, a green plinth and trim bands,
# two rows of small sash windows in each bay (the heritage board's back, as its face's green and cream)
_tb = T_B + 0.03
def _relief(s0, s1, z0, z1, t0, t1, col, kind='plain'):
    """a block standing out of the board's back from t0 to t1 (trim, pilasters, window frames): its face, top, underside
    and ends, so every edge has real depth (no painted-on detail, director 2026-11-22)"""
    for q in ((W(s0, t1, z0), W(s1, t1, z0), W(s1, t1, z1), W(s0, t1, z1)), (W(s0, t0, z1), W(s1, t0, z1), W(s1, t1, z1), W(s0, t1, z1)),
              (W(s0, t0, z0), W(s1, t0, z0), W(s1, t1, z0), W(s0, t1, z0)), (W(s0, t0, z0), W(s0, t1, z0), W(s0, t1, z1), W(s0, t0, z1)),
              (W(s1, t0, z0), W(s1, t1, z0), W(s1, t1, z1), W(s1, t0, z1))):
        m.quad(*q, col, kind)
_relief(0, S_TW, zb, zb + 1.0, T_B, _tb + 0.06, SB_GREEN)                     # plinth
for _z in (Z_VER - 0.15, Z_CORN - 0.45):
    _relief(0, S_TW, _z, _z + 0.3, T_B, _tb + 0.06, SB_GREEN)                  # trim bands
_bays = np.linspace(0, S_TW, 6)
for _s in _bays:
    _relief(max(_s - 0.2, 0), min(_s + 0.2, S_TW), zb, Z_CORN, T_B, _tb + 0.12, SB_GREEN)   # pilasters
for _a, _b in zip(_bays[:-1], _bays[1:]):
    for _zw in (zb + 4.6, zb + 8.0):
        for _k in (0.3, 0.62):
            _c = _a + (_b - _a) * _k
            # sash window: dark glass on the wall, a cream architrave 0.1 m proud round it and a deeper sill
            wallq(_c + 0.38, _tb, _c - 0.38, _tb, _zw, _zw + 1.5, (40, 46, 50), 'plain')
            for _f in ((_c - 0.5, _c - 0.38, _zw, _zw + 1.5), (_c + 0.38, _c + 0.5, _zw, _zw + 1.5), (_c - 0.5, _c + 0.5, _zw + 1.5, _zw + 1.62)):
                _relief(_f[0], _f[1], _f[2], _f[3], T_B, _tb + 0.10, SB_CREAM)
            _relief(_c - 0.58, _c + 0.58, _zw - 0.12, _zw, T_B, _tb + 0.16, SB_CREAM)   # sill
            _relief(_c - 0.38, _c + 0.38, _zw + 0.72, _zw + 0.78, T_B, _tb + 0.05, SB_CREAM)  # meeting rail
wallq(0, T_B, 0, T_F, zb, Z_CORN, SB_TOWER, 'timber')
wallq(0, T_F, S_TW, T_F, zb, Z_VER, (60, 64, 58), 'plain')        # wall behind the verandah
# tower: brick base to the verandah roof, cream weatherboard above (c01, c09)
for (s0, t0, s1, t1) in ((LS, 0.0, LS, T_B), (LS, T_B, S_BR, T_B), (S_BR, 0.0, S_BR, T_F)):
    wallq(s0, t0, s1, t1, zb, Z_VER, SB_BRICK, 'brick')
# the brick base's face with its arched doorway cut through it (c09, c11; never painted on, director 2026-11-22):
# columns from the path (or the arch's crown over the opening) up to the verandah, brick reveals 0.35 m deep, the
# dark door at their back
_D0, _D1, _DJ, _DD = 16.1, 17.3, 1.9, 0.35; _dr = (_D1 - _D0) / 2; _dc = (_D0 + _D1) / 2
_aq = np.linspace(math.pi, 0, 13); _ss = sorted({S_BR, LS, _D0, _D1} | {_dc + _dr * math.cos(q) for q in _aq})
def _dbot(x, xm): return zb + _DJ + math.sqrt(max(0.0, _dr * _dr - (x - _dc) ** 2)) if abs(xm - _dc) < _dr else zb
for _a, _b in zip(_ss[:-1], _ss[1:]):
    if _b - _a < 1e-4: continue
    _m = (_a + _b) / 2; m.quad(W(_a, 0.0, _dbot(_a, _m)), W(_b, 0.0, _dbot(_b, _m)), W(_b, 0.0, Z_VER), W(_a, 0.0, Z_VER), SB_BRICK, 'brick')
_ol = [(_D0, zb)] + [(_dc + _dr * math.cos(q), zb + _DJ + _dr * math.sin(q)) for q in _aq] + [(_D1, zb)]
for (_s0, _z0), (_s1, _z1) in zip(_ol[:-1], _ol[1:]):
    m.quad(W(_s0, 0.0, _z0), W(_s1, 0.0, _z1), W(_s1, _DD, _z1), W(_s0, _DD, _z0), SB_BRICK, 'brick')
m.add([W(_s, _DD, _z) for _s, _z in _ol], [(0, i, i + 1) for i in range(1, len(_ol) - 1)], [(40, 36, 34)] * len(_ol), [(_s, _z) for _s, _z in _ol], 'plain')
for (s0, t0, s1, t1) in ((S_TW, TTW, LS, TTW), (LS, TTW, LS, T_B), (LS, T_B, S_TW, T_B), (S_TW, TTW, S_TW, T_F)):
    wallq(s0, t0, s1, t1, Z_VER, Z_CORN, SB_TOWER, 'timber')
m.quad(W(S_BR, 0, Z_VER), W(LS, 0, Z_VER), W(LS, T_F, Z_VER), W(S_BR, T_F, Z_VER), SB_ROOF, 'plain')
# arched doorway in the brick base (c09, c11), louvred windows in the tower (c01)
for zw in (zb + 6.3, zb + 10.5):   # louvred windows: a dark opening behind five real slats and a frame, on the front and the side
    wallq(S_TW + 0.5, TTW - 0.01, LS - 0.5, TTW - 0.01, zw, zw + 1.0, (30, 30, 28), 'plain')
    wallq(LS + 0.01, 1.5, LS + 0.01, 2.7, zw, zw + 1.0, (30, 30, 28), 'plain')
    for _k in range(5):
        _z = zw + 0.1 + _k * 0.19
        _relief(S_TW + 0.5, LS - 0.5, _z, _z + 0.07, TTW - 0.02, TTW - 0.1, (46, 46, 44))
        _relief(LS + 0.02, LS + 0.1, _z, _z + 0.07, 1.5, 2.7, (46, 46, 44))
    for _a, _b, _c, _d in ((S_TW + 0.4, S_TW + 0.5, TTW, TTW - 0.12), (LS - 0.5, LS - 0.4, TTW, TTW - 0.12)):
        _relief(_a, _b, zw - 0.1, zw + 1.1, _c, _d, SB_CREAM)
    for _a, _b in ((1.4, 1.5), (2.7, 2.8)):
        _relief(LS, LS + 0.12, zw - 0.1, zw + 1.1, _a, _b, SB_CREAM)
# verandah: red roof, cream arched frieze, green posts, green palisade below (sponsor board left out)
m.quad(W(-1.4, -0.3, Z_VER), W(S_BR, -0.3, Z_VER), W(S_BR, T_F, Z_VER + 0.1), W(-1.4, T_F, Z_VER + 0.1), SB_ROOF, 'plain')   # meets the board at z 3.3 (c11)
wallq(-1.4, -0.3, S_BR, -0.3, Z_VER - 0.25, Z_VER, SB_GREEN, 'plain')
wallq(-1.4, 0.0, S_BR, 0.0, Z_VER - 1.0, Z_VER - 0.25, SB_CREAM, 'plain')
for i in range(7):                                                   # six arches between posts
    s = -1.4 + i * (S_BR + 1.4) / 6; box3(m, W(s, 0.1, 0)[:2], U, N, 0.22, 0.22, zb, Z_VER - 0.25, SB_GREEN, 'plain')
wallq(-1.4, 0.05, S_BR, 0.05, zb, zb + 1.6, SB_GREEN, 'fins')
# cornice with brackets, cream parapet with green posts, clock pediment, weathervane (c01, c11)
CO, CS = 0.9, 0.35                  # cornice overhang: 0.9 at the front, 0.35 at the ends and back (c09)
def slab(s0, s1, t0, t1):
    for z, col in ((Z_CORN, SB_GREEN), (Z_CORN + 0.45, SB_CREAM)):
        m.quad(W(s0, t0, z), W(s1, t0, z), W(s1, t1, z), W(s0, t1, z), col, 'plain')
    for (a, b, c, d) in ((s0, t0, s1, t0), (s1, t0, s1, t1), (s1, t1, s0, t1), (s0, t1, s0, t0)):
        wallq(a, b, c, d, Z_CORN, Z_CORN + 0.45, SB_GREEN, 'plain')
slab(-CS, S_TW, T_F - CO, T_B + CS)                 # over the board
slab(S_TW, LS + CS, TTW - CO, T_B + CS)             # over the tower
for s in (1.3, 2.0, 2.72, 3.43, 4.16, 6.97, 7.71, 8.45, 9.21, 9.95, 12.85, 13.61, 14.37, 15.1, 15.85):   # c11: three groups of five
    m.quad(W(s - 0.14, T_F - 0.02, Z_CORN - 0.6), W(s + 0.14, T_F - 0.02, Z_CORN - 0.6), W(s + 0.14, T_F - CO + 0.1, Z_CORN), W(s - 0.14, T_F - CO + 0.1, Z_CORN), (206, 200, 164), 'plain')
# parapet: the front's top line traced off c11 (colour edge, back-projected to the face): two low humps with
# three-slot ornaments, the clock block with sloping shoulders, an arched end over the tower; dark cap moulding
PROF = [(-0.3, 12.95), (1.6, 12.95), (2.2, 13.0), (3.0, 13.12), (3.8, 13.0), (4.4, 12.95), (13.3, 12.95), (13.9, 13.05), (14.6, 13.35), (15.4, 13.08), (15.9, 12.95), (17.7, 12.95)] +        [(18.2 - 0.5 * math.cos(a), 12.95 + 0.5 * math.sin(a)) for a in np.linspace(0.15, math.pi - 0.15, 9)] +        [(18.7, 12.95), (LS + 0.3, 12.95)]
PROF = [(a, zb + b) for a, b in PROF]
def clip(P, lo, hi):
    xs = np.array([a for a, _ in P]); hs = np.array([h for _, h in P])
    keep = [(a, h) for a, h in P if lo < a < hi]
    return [(lo, float(np.interp(lo, xs, hs)))] + keep + [(hi, float(np.interp(hi, xs, hs)))]
for P, tf in ((clip(PROF, -0.3, S_TW), TPAR), (clip(PROF, S_TW, LS + 0.3), TT)):
    for t in (tf, tf + 0.4):
        for (a0, h0), (a1, h1) in zip(P[:-1], P[1:]):
            m.quad(W(a0, t, Z_CORN + 0.45), W(a1, t, Z_CORN + 0.45), W(a1, t, h1), W(a0, t, h0), SB_CREAM, 'plain')
    for (a0, h0), (a1, h1) in zip(P[:-1], P[1:]):
        m.quad(W(a0, tf - 0.12, h0), W(a1, tf - 0.12, h1), W(a1, tf + 0.4, h1 + 0.15), W(a0, tf + 0.4, h0 + 0.15), SB_GREEN, 'plain')
        m.quad(W(a0, tf - 0.12, h0 - 0.02), W(a1, tf - 0.12, h1 - 0.02), W(a1, tf - 0.12, h1 + 0.15), W(a0, tf - 0.12, h0 + 0.15), SB_GREEN, 'plain')
for (s0, t0, s1, t1) in ((S_TW, TT, S_TW, TPAR), (LS + 0.3, TT, LS + 0.3, T_B), (LS + 0.3, T_B, -0.3, T_B), (-0.3, T_B, -0.3, TPAR)):
    wallq(s0, t0, s1, t1, Z_CORN + 0.45, Z_PAR, SB_CREAM, 'plain')
for s in (0.3, 4.3, 13.05, 16.1, 17.45, LS + 0.1):                  # urn-capped posts (c11; c09 for depth)
    tp = TPAR if s < S_TW else TT
    box3(m, W(s, tp + 0.1, 0)[:2], U, N, 0.45, 0.45, Z_CORN + 0.45, zb + 13.45, SB_GREEN, 'plain')
    box3(m, W(s, tp + 0.1, 0)[:2], U, N, 0.7, 0.7, zb + 13.45, zb + 13.6, SB_GREEN, 'plain')
# floodlights for the board face on short poles above the parapet, arms reaching forward (c09 back-projected at z 13.8)
for (sr, tr, sl) in ((0.33, TPAR, -0.35), (5.76, TPAR, 4.98), (11.37, TPAR, 10.54), (16.3, 1.0, 15.4)):
    zr = zb + 13.8
    beam(m, W(sr, tr, Z_PAR), W(sr, tr, zr), 0.08, (60, 64, 62), 'steel')
    beam(m, W(sr, tr, zr), W(sl, tr - 1.8, zr), 0.07, (60, 64, 62), 'steel')
    box3(m, W(sl, tr - 1.8, 0)[:2], U, N, 0.6, 0.45, zr - 0.25, zr - 0.05, (48, 50, 50), 'steel')
for s in (2.65, 3.05, 3.45, 14.15, 14.55, 14.95):                    # three-slot ornaments on the humps
    wallq(s - 0.06, TPAR - 0.03, s + 0.06, TPAR - 0.03, zb + 12.4, zb + 12.85, (236, 232, 222), 'plain')
# clock pediment: its own wall set back on the roof (c09 puts the clock at t 1.7); outline from c11 back-projected there
TP = 1.55                          # c09: the clock back-projects to t 1.52, just proud of the parapet
PED = [(5.07, 12.95), (5.78, 13.33), (6.6, 13.74), (7.52, 14.02), (7.53, 14.92), (9.95, 14.92), (9.96, 13.89),
       (10.67, 13.82), (11.48, 13.59), (12.39, 13.14), (12.6, 12.95)]
PED = [(a, zb + b) for a, b in PED]
for t in (TP, TPAR + 0.4):
    for (a0, h0), (a1, h1) in zip(PED[:-1], PED[1:]):
        m.quad(W(a0, t, Z_CORN + 0.45), W(a1, t, Z_CORN + 0.45), W(a1, t, h1), W(a0, t, h0), SB_CREAM, 'plain')
for (a0, h0), (a1, h1) in zip(PED[:-1], PED[1:]):
    m.quad(W(a0, TP - 0.12, h0), W(a1, TP - 0.12, h1), W(a1, TPAR + 0.52, h1 + 0.15), W(a0, TPAR + 0.52, h0 + 0.15), SB_GREEN, 'plain')
    m.quad(W(a0, TP - 0.12, h0 - 0.02), W(a1, TP - 0.12, h1 - 0.02), W(a1, TP - 0.12, h1 + 0.15), W(a0, TP - 0.12, h0 + 0.15), SB_GREEN, 'plain')
cz, cs = zb + 13.52, 8.75; ang = np.linspace(0, 2 * math.pi, 25)
m.add([W(cs, TP - 0.06, cz)] + [W(cs + 0.64 * math.cos(q), TP - 0.06, cz + 0.64 * math.sin(q)) for q in ang],
      [(0, i + 1, i + 2) for i in range(24)] + [(0, i + 2, i + 1) for i in range(24)], [(236, 234, 226)] * 26,
      [(0, 0)] * 26, 'plain')
m.add([W(cs + 0.78 * math.cos(q), TP - 0.04, cz + 0.78 * math.sin(q)) for q in ang] + [W(cs, TP - 0.04, cz)],
      [(25, i + 1, i) for i in range(24)] + [(25, i, i + 1) for i in range(24)], [(52, 66, 64)] * 26, [(0, 0)] * 26, 'plain')
beam(m, W(cs, TP + 0.25, Z_PED), W(cs, TP + 0.25, Z_VANE), 0.08, (176, 140, 60), 'steel')
box3(m, W(cs, TP + 0.25, 0)[:2], U, N, 0.45, 0.45, Z_VANE - 1.6, Z_VANE - 1.15, (196, 156, 60), 'steel')
beam(m, W(cs - 0.9, TP + 0.25, Z_VANE - 0.6), W(cs + 0.9, TP + 0.25, Z_VANE - 0.6), 0.06, (176, 140, 60), 'steel')
beam(m, W(18.2, 1.5, Z_PAR), W(18.2, 1.5, zb + 16.2), 0.07, (220, 220, 216), 'steel')   # flagpole on the tower (c11)
# raking strut behind the tower (c01, c09)
beam(m, W(LS - 1.2, T_B, Z_CORN - 3.0), W(LS - 1.2, LT, zb), 0.45, SB_CREAM, 'plain')
# amenities box behind the tower's east end: s 19.1-21.8 (c11 face-on), t 4.3-10.2 and 3.0 m high (c09 back-projected)
box3(m, (SB[0] + U * 20.45 + N * 7.25), U, N, 2.7, 5.9, zb - 0.1, zb + 3.0, (118, 116, 110), 'concrete', top=(150, 150, 146))

# ---------------------------------------------------------------- big screen (Esri shadow + photo fit; c00, c09, c11)
# frame corners fitted to c09 (4 corners) and c11 (east edge), max 10 px; heading east-west as the Esri shadow edge
SC_C = np.array([-0.1, 122.29]); _a = 0.0; SU = np.array([math.cos(_a), math.sin(_a)]); SN = np.array([-SU[1], SU[0]])
zs = float(hill_z(SC_C[None])[0]); Z0, Z1, SWID = 6.63, 16.62, 19.08
def solid(m, c, u, n, su, sn, z0, z1, col, kind):
    """closed box, every face drawn both ways: reads as a solid from any side, never as a sheet"""
    c = np.asarray(c, float); P = [c - u * su / 2 - n * sn / 2, c + u * su / 2 - n * sn / 2, c + u * su / 2 + n * sn / 2, c - u * su / 2 + n * sn / 2]
    Q = [(*p, z0) for p in P] + [(*p, z1) for p in P]
    F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (3, 2, 1, 0)]
    m.add(Q, F + [f[::-1] for f in F], [col] * 8, [(q[0], q[2] + q[1]) for q in Q], kind)
# the screen: a 1.8 m deep steel cabinet (c00 side view), a dark bezel standing 0.2 m proud round the face, the face
# itself recessed in it, louvred service panels on the back
solid(m, SC_C + SN * 0.9, SU, SN, SWID, 1.8, Z0, Z1, STEEL, 'steel')
for (x0, x1, za, zb_) in ((-SWID / 2, SWID / 2, Z0, Z0 + 0.35), (-SWID / 2, SWID / 2, Z1 - 0.35, Z1),
                          (-SWID / 2, -SWID / 2 + 0.35, Z0, Z1), (SWID / 2 - 0.35, SWID / 2, Z0, Z1)):
    solid(m, SC_C + SU * (x0 + x1) / 2 - SN * 0.1, SU, SN, x1 - x0, 0.2, za, zb_, (34, 36, 38), 'steel')
m.quad((*(SC_C - SU * (SWID / 2 - 0.35) - SN * 0.02), Z0 + 0.35), (*(SC_C + SU * (SWID / 2 - 0.35) - SN * 0.02), Z0 + 0.35),
       (*(SC_C + SU * (SWID / 2 - 0.35) - SN * 0.02), Z1 - 0.35), (*(SC_C - SU * (SWID / 2 - 0.35) - SN * 0.02), Z1 - 0.35), SCREEN, 'plain')   # matte: a switched-off LED face, not glass (glass mirrored the sky purple)
for x in np.arange(-SWID / 2 + 1.0, SWID / 2 - 0.5, 2.4):       # back panels
    m.quad((*(SC_C + SU * x + SN * 1.82), Z0 + 0.6), (*(SC_C + SU * (x + 2.0) + SN * 1.82), Z0 + 0.6),
           (*(SC_C + SU * (x + 2.0) + SN * 1.82), Z1 - 0.6), (*(SC_C + SU * x + SN * 1.82), Z1 - 0.6), (52, 54, 56), 'fins')
for x in (-7.0, 0.0, 7.0):                       # three leg frames with braces (c00)
    for t in (0.3, 1.5):
        beam(m, (*(SC_C + SU * x + SN * t), zs), (*(SC_C + SU * x + SN * t), Z0), 0.45, STEEL, 'steel')
    beam(m, (*(SC_C + SU * x + SN * 0.3), zs), (*(SC_C + SU * (x + 2.0) + SN * 1.5), Z0), 0.2, STEEL, 'steel')
    solid(m, SC_C + SU * x + SN * 0.9, SU, SN, 1.0, 2.0, zs - 0.2, zs + 0.3, (150, 150, 146), 'concrete')   # footing
# paved apron under the screen
ap = SC_C + np.array([[-10.5, -2.5], [10.5, -2.5], [10.5, 2.6], [-10.5, 2.6]])
m.quad(*[(*p, zs + 0.02) for p in ap], PAVE, 'paving')
m.save('hill')
print('hill', len(m.v), 'verts', len(m.f), 'faces', 'base z', round(zb, 2), 'screen z', round(zs, 2))
