"""Oval Hotel + East Gate (east stand front) -> model/hotel.ply.
Footprint: COX lodged plan Level 4 (h10), outer facade traced by tools/hoteltrace.py (grid/hotel_outer.json), plan px ->
model metres by tools/planreg.py. Heights: plan RLs (plaza L1 = 0; L2 3.6, L3 7.2, L4.1 10.4, L4.2 13.6, L5 16.8, roof 20).
Facade layout, materials and colours read from photo C (close/east_gate_2023.jpg) and photos/hotel_*_2020.jpg.
Every surface carries a hand-made material kind (no photo pixels)."""
import json, os, sys
import numpy as np
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.spatial import Delaunay
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from planreg import pl2m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'model')
KIND = {'plain': 0, 'seats': 1, 'concrete': 2, 'roof': 3, 'steel': 4, 'glass': 5, 'brick': 6, 'grass': 7, 'fins': 8,
        'timber': 9, 'copper': 10, 'stone': 11}
PC = np.array([0.0, 0.0])
SLABS = [3.6, 7.2, 10.4, 13.6, 16.8, 20.0]

# material colours (daylight, read from the photos)
# copper and brick measured on photo C sunlit faces (render/photo ratio)
COPPER = (146, 121, 110); BRICK = (196, 138, 110); BLACK = (30, 30, 32); STONE = (196, 186, 166)
GLASS = (60, 80, 100); PALE = (205, 200, 190); SOFFIT = (70, 70, 72); PANEL = (98, 100, 102); BACK = (180, 178, 172)


class Mesh:
    def __init__(s): s.v = []; s.c = []; s.f = []; s.uv = []; s.k = []
    def add(s, V, F, C, UV, kind):
        o = len(s.v); s.v += [tuple(x) for x in V]; s.c += [tuple(x) for x in C]; s.uv += [tuple(x) for x in UV]
        s.k += [KIND[kind]] * len(V); s.f += [tuple(o + i for i in f) for f in F]
    def quad(s, a, b, c, d, col, kind, uv):
        s.add([a, b, c, d], [(0, 1, 2, 3)], [col] * 4, uv, kind)
    def save(s, name):
        hdr = ['ply', 'format ascii 1.0', 'element vertex %d' % len(s.v)] + ['property float ' + c for c in 'xyzst'] + \
              ['property uchar ' + c for c in ('red', 'green', 'blue', 'alpha')] + \
              ['element face %d' % len(s.f), 'property list uchar int vertex_indices', 'end_header']
        with open(os.path.join(OUT, name + '.ply'), 'w', newline='') as fh:
            fh.write('\n'.join(hdr) + '\n')
            for v, uv, c, k in zip(s.v, s.uv, s.c, s.k):
                fh.write('%.3f %.3f %.3f %.3f %.3f %d %d %d %d\n' % (*v, *uv, *[int(x) for x in c], k * 20))
            for f in s.f: fh.write('%d %s\n' % (len(f), ' '.join(map(str, f))))


# ---------- footprint ----------
T = np.array(json.load(open(os.path.join(ROOT, 'grid/hotel_outer.json'))), float)
T[:, 1] = median_filter(T[:, 1], 5, mode='nearest')


def outer(u0, u1, step=0.4, vfix=None, sigma=0.0):
    """outer facade polyline (model metres, resampled every `step`) for plan u0..u1, south -> north"""
    sel = T[(T[:, 0] >= u0) & (T[:, 0] <= u1)]
    u = np.r_[u0, sel[:, 0], u1]; v = np.r_[sel[0, 1], sel[:, 1], sel[-1, 1]] if vfix is None else np.full(len(sel) + 2, vfix)
    x, y = pl2m(u, v); P = np.c_[x, y]
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, L[-1], max(2, int(L[-1] / step) + 1))
    Q = np.c_[np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])]
    if sigma > 0: Q = gaussian_filter1d(Q, sigma / step, axis=0, mode='nearest')   # smooth curved copper/plan trace jitter
    return Q


def normals(P):
    t = gaussian_filter1d(np.gradient(P, axis=0), 3.0 / 0.4, axis=0, mode='nearest')  # ~3 m smoothing: the plan trace's
    t /= np.linalg.norm(t, axis=1)[:, None]                                                  # jitter folded the roof's back line
    n = np.c_[t[:, 1], -t[:, 0]]
    if np.mean(np.sum(n * (P - PC), 1)) < 0: n = -n
    # smooth so the saw-tooth steps don't fold the back line
    return n


def arclen(P): return np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]


# ---------- builders ----------
def facade(m, P, n, zs, cell, inset_depth=0.15):
    """outer facade of polyline P (normals n) on rows zs; cell(s, sfrac, z0, z1) -> (kind, col, inset) per cell"""
    S = arclen(P); Ltot = S[-1]
    for i in range(len(P) - 1):
        sm = (S[i] + S[i + 1]) / 2
        for z0, z1 in zip(zs[:-1], zs[1:]):
            kind, col, ins = cell(sm, sm / Ltot, z0, z1)
            a, b = P[i] - n[i] * ins, P[i + 1] - n[i + 1] * ins
            m.quad((*a, z0), (*b, z0), (*b, z1), (*a, z1), col, kind, [(S[i], z0), (S[i + 1], z0), (S[i + 1], z1), (S[i], z1)])
            if ins > 0:  # reveals back to the wall plane
                A, B = P[i], P[i + 1]
                m.quad((*A, z1), (*B, z1), (*b, z1), (*a, z1), col, kind, [(S[i], 0), (S[i + 1], 0), (S[i + 1], ins), (S[i], ins)])
                if z0 > 0.01:  # no floor strip at ground level (it z-fought the lawn)
                    m.quad((*a, z0), (*b, z0), (*B, z0), (*A, z0), col, kind, [(S[i], 0), (S[i + 1], 0), (S[i + 1], ins), (S[i], ins)])


def reveal_sides(m, P, n, zs, cell):
    """vertical reveal faces where inset changes between neighbouring cells"""
    S = arclen(P)
    for i in range(1, len(P) - 1):
        sl, sr = (S[i - 1] + S[i]) / 2, (S[i] + S[i + 1]) / 2
        for z0, z1 in zip(zs[:-1], zs[1:]):
            kl, cl, il = cell(sl, sl / S[-1], z0, z1); kr, cr, ir = cell(sr, sr / S[-1], z0, z1)
            if abs(il - ir) < 1e-6: continue
            lo, hi = min(il, ir), max(il, ir); col, kind = (cl, kl) if il < ir else (cr, kr)
            a, b = P[i] - n[i] * lo, P[i] - n[i] * hi
            m.quad((*a, z0), (*b, z0), (*b, z1), (*a, z1), col, kind, [(0, z0), (hi - lo, z0), (hi - lo, z1), (0, z1)])


def ribbon(m, P, n, z0, z1, out, col, kind='steel'):
    """slab edge / frame band: front face `out` m proud of the facade, with top and bottom"""
    S = arclen(P); Q = P + n * out
    for i in range(len(P) - 1):
        a, b, A, B = Q[i], Q[i + 1], P[i], P[i + 1]
        uv = [(S[i], z0), (S[i + 1], z0), (S[i + 1], z1), (S[i], z1)]
        m.quad((*a, z0), (*b, z0), (*b, z1), (*a, z1), col, kind, uv)
        m.quad((*A, z1), (*a, z1), (*b, z1), (*B, z1), col, kind, uv)
        m.quad((*A, z0), (*B, z0), (*b, z0), (*a, z0), col, kind, uv)


def prism_shell(m, P, n, depth, z0, z1, col, kind, top_col=None, top_kind='concrete', bottom=False):
    """back wall, end caps and roof of the block behind facade P (the facade itself is built by facade())"""
    Bk = P - n * depth; S = arclen(P)
    if len(Bk) > 8:  # an inward offset of a kinked trace folds; smooth the back line (~4 m) so the top's back edge is clean
        Bk = gaussian_filter1d(Bk, 4.0 / max(S[-1] / (len(P) - 1), 1e-3), axis=0, mode='nearest')
    for i in range(len(P) - 1):  # back wall (faces the stand)
        a, b = Bk[i], Bk[i + 1]
        m.quad((*b, z0), (*a, z0), (*a, z1), (*b, z1), BACK, 'concrete', [(S[i + 1], z0), (S[i], z0), (S[i], z1), (S[i + 1], z1)])
    for A, B_, flip in ((P[0], Bk[0], False), (P[-1], Bk[-1], True)):  # end caps
        q = [(*A, z0), (*B_, z0), (*B_, z1), (*A, z1)]
        if flip: q = q[::-1]
        d = np.linalg.norm(A - B_)
        m.quad(*q, col, kind, [(0, z0), (d, z0), (d, z1), (0, z1)][::-1 if flip else 1])
    poly = np.r_[P, Bk[::-1]]
    for z, up in ((z1, True),) + (((z0, False),) if bottom else ()):
        tri = Delaunay(poly).simplices; cen = poly[tri].mean(1); tri = tri[Path(poly).contains_points(cen)]
        V = np.c_[poly, np.full(len(poly), z)]
        F = [tuple(t) if up == ccw_tri(poly, t) else tuple(t[::-1]) for t in tri]
        m.add(V, F, [top_col or col] * len(V), poly, top_kind if up else 'concrete')


def ccw_tri(P, t):
    a, b, c = P[t[0]], P[t[1]], P[t[2]]
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) > 0


def box(m, a, b, w, col, kind):
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); d /= L
    u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0])
    v = np.cross(u, d); h = w / 2; off = [(-h, -h), (h, -h), (h, h), (-h, h)]
    V = [a + x * u + y * v for x, y in off] + [b + x * u + y * v for x, y in off]
    F = [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)] + [(3, 2, 1, 0), (4, 5, 6, 7)]
    m.add(V, F, [col] * 8, [(i * w, 0) for i in range(4)] + [(i * w, L) for i in range(4)], kind)


def column(m, c, z0, z1, r, col, kind, k=16):
    V = []; F = []; UV = []
    for j in range(k + 1):
        a = 2 * np.pi * j / k
        for z in (z0, z1): V.append((c[0] + r * np.cos(a), c[1] + r * np.sin(a), z)); UV.append((r * a, z))
    for j in range(k): F.append((2 * j, 2 * j + 2, 2 * j + 3, 2 * j + 1))
    m.add(V, F, [col] * len(V), UV, kind)


def in_any(f, spans): return any(a <= f < b for a, b in spans)


m = Mesh()

# ---------- copper blocks (south u 1442-1880, north 3085-3515) ----------
# windows per storey as fractions of the block's facade length, read from photo C (south: 3 windows, north: 3)
BLOCKS = [(1442, 1905, [(0.155, 0.29), (0.32, 0.48), (0.70, 0.81)], [(0.25, 0.32), (0.69, 0.81), (0.82, 0.88)]),
          (3085, 3515, [(0.10, 0.16), (0.47, 0.57), (0.78, 0.88)], [])]   # ground-floor service doors from photo C (north hidden by trees)
DOOR = (138, 140, 140)
for u0, u1, wins, doors in BLOCKS:
    P = outer(u0, u1, sigma=1.2); n = normals(P)
    def cell(s, f, z0, z1, wins=wins, doors=doors):
        if z1 <= 2.6 and in_any(f, doors): return ('steel', DOOR, 2.0)      # grey service doors in the recess
        if z1 <= 3.6: return ('concrete', PALE, 2.0)                       # recessed ground floor
        if in_any(f, wins) and z0 >= 3.6 + 0.3 and z1 <= 20 - 0.3: return ('glass', GLASS, 0.12)
        return ('copper', COPPER, 0.0)
    zs = [0.0, 2.6, 3.6]
    for a, b in zip(SLABS[:-1], SLABS[1:]): zs += [a + 0.35, b - 0.35, b]
    zs = sorted(set(zs))
    facade(m, P, n, zs, cell); reveal_sides(m, P, n, zs, cell)
    for z in SLABS[:-1]: ribbon(m, P, n, z - 0.12, z + 0.28, 0.25, BLACK)          # black floor frames
    ribbon(m, P, n, 19.7, 20.4, 0.3, BLACK)                                          # roof frame
    ribbon(m, P - n * 2.0, n, 3.0, 3.6, 2.0, COPPER, 'copper')                       # copper-clad fascia over the recess (photo C)
    prism_shell(m, P, n, 12.0, 0.0, 20.4, COPPER, 'copper', (90, 90, 92))
    for f in (0.02, 0.98):  # corner columns under the block
        i = int(f * (len(P) - 1)); column(m, P[i] - n[i] * 0.5, 0, 3.6, 0.35, PALE, 'concrete')

# ---------- brick wings (south u 504-1442, north 3515-4460) ----------
ROOM = 3.8
for u0, u1 in ((504, 1442), (3515, 4460)):
    P = outer(u0, u1, sigma=4.0); n = normals(P)   # smoothed: the raw plan trace left a ragged roof edge
    def cell(s, f, z0, z1):
        if z1 <= 3.6: return ('glass', GLASS, 3.0)                          # recessed glazed ground floor
        if z0 >= 16.8: return ('glass', GLASS, 0.6)                         # glazed top floor under the roof
        r = s % ROOM; fl = z0 - max(z for z in [3.6] + SLABS if z <= z0 + 1e-6)
        win = 1.15 <= r < 2.65 and 0.9 <= fl < 2.9
        frame = 1.0 <= r < 2.8 and 0.75 <= fl < 3.05
        if win: return ('glass', GLASS, 0.18)
        if frame: return ('copper', COPPER, 0.0)
        return ('brick', BRICK, 0.0)
    zs = [0.0, 3.6]
    for a in SLABS[:4]: zs += [a + 0.75, a + 0.9, a + 2.9, a + 3.05]
    zs += [16.8, 20.0]
    zs = sorted(set(round(z, 3) for z in zs))
    # resample on the room grid so window edges fall on vertices
    S = arclen(P); grid = np.unique(np.r_[np.arange(0, S[-1], 0.5), [k * ROOM + e for k in range(int(S[-1] / ROOM) + 1) for e in (1.0, 1.15, 2.65, 2.8)]])
    grid = grid[grid <= S[-1]]; P = np.c_[np.interp(grid, S, P[:, 0]), np.interp(grid, S, P[:, 1])]; n = normals(P)
    facade(m, P, n, zs, cell); reveal_sides(m, P, n, zs, cell)
    ribbon(m, P, n, 20.0, 20.5, 1.5, BLACK)                                          # thin roof overhang
    ribbon(m, P - n * 3.0, n, 3.3, 3.6, 3.0, SOFFIT, 'concrete')
    prism_shell(m, P, n, 10.5, 0.0, 20.5, BRICK, 'brick', (90, 90, 92))
    S = arclen(P)
    for k in range(int(S[-1] / 7.6)):  # V struts under the wing (photos/hotel_2020.jpg)
        s0 = 3.8 + k * 7.6
        if s0 > S[-1] - 2: break
        c = np.interp(s0, S, P[:, 0]), np.interp(s0, S, P[:, 1]); i = np.searchsorted(S, s0); nn = n[min(i, len(n) - 1)]
        t = np.array([-nn[1], nn[0]]); base = np.array(c) - nn * 1.0
        for sg in (-1, 1): box(m, (*base, 0), (*(base + t * 1.8 * sg), 3.3), 0.45, (190, 178, 156), 'concrete')

# ---------- cores: glass strip + banded stone pier ----------
CORES = [(1905, 1980, 'glass'), (1980, 2046, 'pier'), (2902, 2985, 'pier'), (2985, 3085, 'glass')]
for u0, u1, what in CORES:
    P = outer(u0, u1); n = normals(P)
    if what == 'glass':
        cell = lambda s, f, z0, z1: ('glass', (70, 95, 125), 0.3)
        zs = [0, 3.6, 7.2, 10.4, 13.6, 16.8, 20.0]
        facade(m, P, n, zs, cell); prism_shell(m, P - n * 0.3, n, 11.7, 0, 20.0, (70, 95, 125), 'glass', (90, 90, 92))
    else:
        P = P + n * 0.4
        cell = lambda s, f, z0, z1: ('stone', STONE, 0.0)
        facade(m, P, n, [0, 21.6], cell); prism_shell(m, P, n, 12.4, 0, 21.6, STONE, 'stone', STONE, 'stone')

# ---------- East Gate atrium (glass wall on the round-column line) and the cantilevered pod ----------
VA = 1967   # atrium glass line and top read from photo C (tools/fitC14.py), in line with the core glass
P = outer(2046, 2902, vfix=VA); n = normals(P)
facade(m, P, n, [0, 3.6, 7.2, 10.4, 13.6, 17.0, 19.5], lambda s, f, z0, z1: ('glass', (55, 75, 95), 0.0))
ribbon(m, P, n, 19.5, 20.3, 0.2, BLACK)
prism_shell(m, P, n, 14.0, 0, 20.3, (55, 75, 95), 'glass', (90, 90, 92))
# pod: plan "MAT 03" box, v 1865-2107, z 7.2-12; photo C: black frame, glass strip, grey panels, black frame
VP = 2149   # pod front and level read from photo C (fitC14): 1.8 m proud of the plan line, 1 m lower
PZ = -1.0
Pp = outer(2046, 2902, vfix=VP); npod = normals(Pp)
def pcell(s, f, z0, z1):
    if z1 <= 7.7 + PZ or z0 >= 11.4 + PZ: return ('steel', BLACK, 0.0)
    if z1 <= 8.9 + PZ: return ('glass', GLASS, 0.1)
    return ('concrete', PANEL, 0.0)
zs = [z + PZ for z in (7.2, 7.7, 8.9, 11.4, 12.0)]
facade(m, Pp, npod, zs, pcell); reveal_sides(m, Pp, npod, zs, pcell)
D = float(np.mean(np.linalg.norm(Pp - P[np.linspace(0, len(P) - 1, len(Pp)).astype(int)], axis=1)))
prism_shell(m, Pp, npod, D, 7.2 + PZ, 12.0 + PZ, PANEL, 'concrete', (80, 80, 82), 'concrete', bottom=True)
Sp = arclen(Pp)
for f in (0.35, 0.62):  # round columns under the pod (photo C)
    s0 = f * Sp[-1]; i = np.searchsorted(Sp, s0)
    column(m, Pp[i] - npod[i] * 3.0, 0, 7.2 + PZ, 0.35, (40, 40, 42), 'steel')
# fin screen between the south pier and the pod (photo C), L3 level
Pf = outer(1990, 2050, vfix=2085); nf = normals(Pf)
facade(m, Pf, nf, [7.2, 11.2], lambda s, f, z0, z1: ('fins', (52, 52, 55), 0.0))
prism_shell(m, Pf, nf, 4.5, 7.2, 11.2, (52, 52, 55), 'fins', (60, 60, 62), 'concrete', bottom=True)

# ---------- the ground's own signs on the east side (photo C, placed by rays through camC14: tools/signC.py) ----------
from letters import place, ring
NF = np.array([0.98, 0.21, 0.0]); NF /= np.linalg.norm(NF)                      # facade normal (photo C hits)
# 'Adelaide Oval' pylon in front of the pod, north of the atrium: 3.5 m wide, ground to 13.0 m (photo C)
PL, PR = np.array([129.41, 37.87]), np.array([128.67, 41.31]); PD = 1.2
cn = [np.r_[PL, 0], np.r_[PR, 0]]; bk = [c - np.r_[NF[:2] * PD, 0] for c in cn]
for z0, z1, col in ((0.0, 13.0, (190, 186, 178)),):
    q = lambda P, z: (P[0], P[1], z)
    m.quad(q(cn[0], z0), q(cn[1], z0), q(cn[1], z1), q(cn[0], z1), col, 'concrete', [(0, 0)] * 4)
    m.quad(q(bk[1], z0), q(bk[0], z0), q(bk[0], z1), q(bk[1], z1), col, 'concrete', [(0, 0)] * 4)
    m.quad(q(bk[0], z0), q(cn[0], z0), q(cn[0], z1), q(bk[0], z1), col, 'concrete', [(0, 0)] * 4)
    m.quad(q(cn[1], z0), q(bk[1], z0), q(bk[1], z1), q(cn[1], z1), col, 'concrete', [(0, 0)] * 4)
    m.quad(q(cn[0], z1), q(cn[1], z1), q(bk[1], z1), q(bk[0], z1), col, 'concrete', [(0, 0)] * 4)
c0 = (PL + PR) / 2 - NF[:2] * PD / 2; tt = (PR - PL) / np.linalg.norm(PR - PL)   # dark light bracket on top (photo C)
box(m, (*(c0 - tt * 1.2), 13.0), (*(c0 + tt * 1.2), 13.4), PD * 0.6, BLACK, 'steel')
BRONZE = (150, 98, 58)
up = np.array([0, 0, 1.0]); lft = np.r_[(PL - PR) / np.linalg.norm(PL - PR), 0]   # logo reads upward, letter tops face north
o = np.r_[128.78, 40.78, 0] + NF * 0.03                                     # right edge of the lettering at its foot
for txt, b0, b1 in (('Adelaide', 8.10, 10.50), ('val', 11.86, 12.27)):
    V, T = place(txt, o, up, lft, (b0, 0.0, b1, 0.88), 'bold')
    m.add(V, [tuple(x) for x in T], [BRONZE] * len(V), [(0, 0)] * len(V), 'plain')
RG = ring(11.185, 0.445, 0.63, 0.49, 25, 75)   # the ringed O in sign metres (a up, b to the letter tops), open towards 'val' (photo C)
V, T = place(RG, o, up, lft, RG.bounds)
m.add(V, [tuple(x) for x in T], [BRONZE] * len(V), [(0, 0)] * len(V), 'plain')
# 'East Gate' on the atrium glass over the entrance, 0.93 m letters
eo = np.array([123.7, 24.82, 3.59]) + NF * 0.05; ea = np.array([122.56, 30.16, 3.59]) - np.array([123.7, 24.82, 3.59])
EL = np.linalg.norm(ea); ea /= EL
V, T = place('East Gate', eo, ea, up, (0.0, 0.0, EL, 0.93), 'normal')
m.add(V, [tuple(x) for x in T], [(200, 200, 204)] * len(V), [(0, 0)] * len(V), 'plain')

m.save('hotel')
print('hotel.ply', len(m.v), 'verts', len(m.f), 'faces')
