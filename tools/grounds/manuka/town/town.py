"""Manuka Oval's surroundings: the town within 1.1 km, built as geometry, for GroundModels.backdrop().

    python3 tools/grounds/manuka/town/groundmap.py
    python3 tools/grounds/manuka/town/prep.py
    python3 tools/grounds/manuka/town/town.py          # writes assets/grounds/manuka/manuka_backdrop_part1.glb

What is in it (all in the model's metres; glTF x east, y up, z south):
- The ground: the painted map (groundmap.py) draped over the land's real shape (Terrarium heights, smoothed),
  level with the stadium's apron and rising to Capital Hill, Forrest and Red Hill's foot.
- Every building (prep.py): its real footprint and storeys; walls with recessed windows (reveals, sills and
  glass set back), shopfronts on the shops; houses under hipped roofs that follow the plan (each wing its own hip,
  valleys where they meet) with eaves, fascias and soffits; flats and offices under flat roofs with a parapet,
  plant and lift overruns; sheds and garages under skillions. Roof colours measured off the aerial photo.
- Every mature tree the ACT Government's LiDAR found (its crown's outline and height), shaped by species from
  the ACT tree register: oaks, elms and planes round and full, gums open and grey-green with pale trunks, cedars
  and pines dark and conical, Italian cypresses and Lombardy poplars as columns.
Landmarks are modelled by hand in landmarks.py and replace their footprints here.
"""
import colorsys
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASSETS, C, CACHE, HERE, Dem, area  # noqa: E402

R = 1100.0
BLOCK = 275.0
WIN_R = 640.0           # windows modelled within this range of the field (past it a wall is plain)
rng = np.random.default_rng(1929)


# ---------------------------------------------------------------- mesh accumulation
class Acc:
    """Flat-shaded triangles with a colour each, by material and block."""

    def __init__(self):
        self.parts = {}
        self.smooth = {}

    def mesh(self, key, V, F, cols):
        """An indexed piece drawn with smooth normals (tree crowns): V points, F index triples, a colour a point."""
        L = self.smooth.setdefault(key, ([], [], []))
        base = sum(len(v) for v in L[0])
        L[0].append(np.asarray(V, float))
        L[1].append(np.asarray(F, int) + base)
        L[2].append(np.asarray(cols, float))

    def tri(self, key, a, b, c, col):
        L = self.parts.setdefault(key, ([], []))
        L[0].append((a, b, c))
        L[1].append(col)

    def quad(self, key, a, b, c, d, col):
        self.tri(key, a, b, c, col)
        self.tri(key, a, c, d, col)

    def poly(self, key, pts, col):
        """A convex or ear-clippable planar polygon (fan from an ear-clipped triangulation)."""
        for t in earclip(pts):
            self.tri(key, pts[t[0]], pts[t[1]], pts[t[2]], col)


def earclip(pts):
    """Triangles (index triples) of a simple polygon given in 3D (projected on its best plane)."""
    P = np.asarray(pts, float)
    n = np.cross(P[1] - P[0], P[2] - P[0])
    nn = np.zeros(3)
    for i in range(len(P)):
        nn += np.cross(P[i], P[(i + 1) % len(P)])
    ax = int(np.argmax(np.abs(nn)))
    Q = np.delete(P, ax, 1)
    if nn[ax] < 0:
        Q = Q[:, ::-1]
    from shapely.geometry import Polygon
    import shapely
    pg = Polygon(Q)
    if not pg.is_valid or pg.area < 1e-6:
        return []
    tris = shapely.constrained_delaunay_triangles(pg)
    out = []
    idx = {tuple(np.round(q, 6)): i for i, q in enumerate(Q)}
    for t in tris.geoms:
        cs = list(t.exterior.coords)[:3]
        ii = [idx.get(tuple(np.round(c, 6))) for c in cs]
        if None in ii:
            continue
        out.append(ii)
    return out


def block_of(x, y):
    return (int(math.floor(x / BLOCK)), int(math.floor(y / BLOCK)))


# ---------------------------------------------------------------- colours
def srgb(c):
    return tuple(float(v) / 255.0 for v in c)


def dehaze(rgb):
    """The aerial photo's roof colour with its haze taken out: more saturated, a little darker."""
    r, g, b = [v / 255.0 for v in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.1 and (h < 0.13 or h > 0.9):     # tile and terracotta: the photo greys them most
        s = min(0.66, s * 2.4)
        v = v * 0.97
        h = (h - 0.012) % 1.0      # a touch redder: the photo's warm haze yellows the tiles
    else:
        s = min(1.0, s * 1.5)
        v = v * 0.98
    return tuple(int(255 * q) for q in colorsys.hsv_to_rgb(h, s, v))


WALLS_HOUSE = [((214, 200, 170), 4), ((232, 228, 218), 4), ((150, 96, 74), 3), ((176, 112, 86), 2),
               ((196, 160, 126), 3), ((122, 92, 76), 2), ((200, 196, 186), 2), ((168, 150, 128), 1)]
WALLS_FLATS = [((226, 222, 210), 4), ((200, 192, 176), 3), ((170, 168, 162), 2), ((148, 112, 92), 2),
               ((92, 92, 96), 1), ((214, 206, 188), 2)]
WALLS_OFFICE = [((190, 190, 186), 3), ((214, 210, 200), 3), ((140, 142, 146), 2), ((166, 128, 100), 1)]
GLASS = (34, 44, 54)
GLASS_SHOP = (52, 64, 72)
SOFFIT = (206, 204, 198)
FASCIA = (236, 236, 232)
DECK = (132, 132, 128)


def pick(pal, r):
    w = np.array([p[1] for p in pal], float)
    return pal[int(np.searchsorted(np.cumsum(w) / w.sum(), r))][0]


def shade(col, f):
    return tuple(max(0, min(255, int(c * f))) for c in col)


# ---------------------------------------------------------------- the ground
def ground_heights():
    dem = Dem(15, R + 300)
    dem.smooth(3.0)          # Terrarium's 4 m samples carry the odd building and tree: smooth to the land's shape
    return dem


def apron_r():
    """Per half-degree bearing from the field's centre, the radius where the model's apron ends (build.py)."""
    import trimesh
    sc = trimesh.load(os.path.join(ASSETS, "manuka.glb"))
    rad = np.zeros(720)
    # The model is exported unrotated at the origin: glTF x east, y up, z south.
    for node in sc.graph.nodes_geometry:
        T, gname = sc.graph[node]
        v = trimesh.transformations.transform_points(sc.geometry[gname].vertices, T)
        low = v[np.abs(v[:, 1]) < 0.3]
        x, y = low[:, 0] - C[0], -low[:, 2] - C[1]
        b = (np.degrees(np.arctan2(x, y)) % 360 * 2).astype(int) % 720
        np.maximum.at(rad, b, np.hypot(x, y))
    for _ in range(3):
        rad = np.maximum(rad, np.maximum(np.roll(rad, 1), np.roll(rad, -1)))
    return rad


def ground(acc_ground, dem, rad):
    """A polar mesh from just inside the apron's edge to R, z on the land, UVs on the map."""
    nb = 720
    bs = np.arange(nb) * 0.5   # (rad is per half degree)
    rings_ = [0.0]
    while rings_[-1] < 1.0:
        rings_.append(rings_[-1] + 0.004 + rings_[-1] * 0.03)
    t = np.clip(np.array(rings_), 0, 1)
    verts, uvs = [], []
    r_in = rad - 1.2
    for i, f in enumerate(t):
        for j, b in enumerate(bs):
            a = math.radians(b)
            r0 = r_in[j]
            rmax = 1085.0
            rr = r0 + (rmax - r0) * f
            x, y = C[0] + rr * math.sin(a), C[1] + rr * math.cos(a)
            verts.append((x, y, rr))
    V = np.array(verts)
    x, y, rr = V[:, 0], V[:, 1], V[:, 2]
    z = dem.at(x, y)
    d = rr - (r_in[np.tile(np.arange(nb), len(t))])
    w = np.clip((d - 18.0) / 160.0, 0, 1)
    w = w * w * (3 - 2 * w)
    z = z * w - 0.06 * (1 - w)
    u = (x + R) / (2 * R)
    v = (R - y) / (2 * R)
    P = np.c_[x, y, z]
    F = []
    for i in range(len(t) - 1):
        for j in range(nb):
            a0, b0 = i * nb + j, i * nb + (j + 1) % nb
            a1, b1 = (i + 1) * nb + j, (i + 1) * nb + (j + 1) % nb
            F += [(a0, b0, a1), (b0, b1, a1)]
    acc_ground["v"], acc_ground["uv"], acc_ground["f"] = P, np.c_[u, v], np.array(F)
    return P


class Land:
    """Height of the draped ground anywhere (the same blend as ground())."""

    def __init__(self, dem, rad):
        self.dem, self.rad = dem, rad

    def z(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        b = (np.degrees(np.arctan2(x - C[0], y - C[1])) % 360 * 2).astype(int) % 720
        d = np.hypot(x - C[0], y - C[1]) - (self.rad[b] - 1.2)
        w = np.clip((d - 18.0) / 160.0, 0, 1)
        w = w * w * (3 - 2 * w)
        return self.dem.at(x, y) * w - 0.06 * (1 - w)


# ---------------------------------------------------------------- buildings
def ccw_ring(ring):
    return ring if area(ring) > 0 else ring[::-1]


def simplify(ring, tol=0.25):
    from shapely.geometry import Polygon
    pg = Polygon(ring).simplify(tol)
    if pg.geom_type != "Polygon" or pg.area < 4:
        return ring
    return ccw_ring([tuple(p) for p in list(pg.exterior.coords)[:-1]])


STOREY = {"house": 2.75, "flats": 3.0, "office": 3.6, "retail": 4.0, "church": 5.0, "shed": 2.5}
KINDS = {"apartments": "flats", "residential": "flats", "dormitory": "flats", "hotel": "flats",
         "office": "office", "commercial": "office", "civic": "office", "government": "office", "public": "office",
         "school": "office", "hospital": "office", "university": "office", "college": "office", "kindergarten": "office",
         "retail": "retail", "supermarket": "retail", "church": "church", "cathedral": "church", "chapel": "church",
         "garage": "shed", "garages": "shed", "shed": "shed", "carport": "shed", "roof": "shed", "hut": "shed",
         "house": "house", "detached": "house", "semidetached_house": "house", "bungalow": "house", "terrace": "house"}


def wall(acc, key, a, b, z0, z1, col, wins, out):
    """One wall from a to b (plan points), z0 to z1, with windows cut into it: wins is a list of
    (s0, s1, zb, zt) openings along the wall (metres from a) each set 0.14 m into it with reveals and glass."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.hypot(*(b - a)))
    if L < 1e-3:
        return
    t = (b - a) / L
    nrm = np.array([t[1], -t[0]])          # outward for a ccw ring
    def P(s, z, dep=0.0):
        p = a + t * s - nrm * dep
        return (p[0], p[1], z)
    if not wins:
        acc.quad(key, P(0, z0), P(L, z0), P(L, z1), P(0, z1), col)
        return
    # Rows of openings share their bands: split the wall into horizontal bands at every sill and head.
    zs = sorted(set([z0, z1] + [w[2] for w in wins] + [w[3] for w in wins]))
    for za, zb in zip(zs[:-1], zs[1:]):
        if zb - za < 1e-4:
            continue
        cuts = sorted([(w[0], w[1]) for w in wins if w[2] <= za + 1e-4 and w[3] >= zb - 1e-4])
        s = 0.0
        for s0, s1 in cuts:
            if s0 > s:
                acc.quad(key, P(s, za), P(s0, za), P(s0, zb), P(s, zb), col)
            s = max(s, s1)
        if s < L:
            acc.quad(key, P(s, za), P(L, za), P(L, zb), P(s, zb), col)
    rev = shade(col, 0.78)
    dep = 0.14
    for s0, s1, zb, zt in wins:
        glass = GLASS_SHOP if zt - zb > 2.2 else GLASS
        acc.quad(key, P(s0, zb, dep), P(s1, zb, dep), P(s1, zt, dep), P(s0, zt, dep), glass)   # glass, set back
        acc.quad(key, P(s0, zt), P(s1, zt), P(s1, zt, dep), P(s0, zt, dep), rev)                # head
        acc.quad(key, P(s0, zb, dep), P(s1, zb, dep), P(s1, zb), P(s0, zb), shade(col, 1.06))  # sill
        acc.quad(key, P(s0, zb), P(s0, zb, dep), P(s0, zt, dep), P(s0, zt), rev)                # jambs
        acc.quad(key, P(s1, zb, dep), P(s1, zb), P(s1, zt), P(s1, zt, dep), rev)
        if zt - zb > 1.0 and s1 - s0 > 1.9:            # a mullion down the middle of a wide window
            m = (s0 + s1) / 2
            acc.quad(key, P(m - 0.04, zb, dep - 0.02), P(m + 0.04, zb, dep - 0.02), P(m + 0.04, zt, dep - 0.02),
                     P(m - 0.04, zt, dep - 0.02), FASCIA)


def window_layout(L, kind, storeys, floor_z, sh, eave, shopfront):
    """Openings along a wall of length L."""
    wins = []
    if L < 2.2:
        return wins
    spec = {"house": (1.5, 1.25, 0.95, 4.2), "flats": (1.6, 1.5, 0.9, 3.4), "office": (2.2, 1.7, 0.9, 2.9),
            "retail": (2.2, 1.7, 1.0, 3.2), "church": (1.0, 2.6, 1.6, 4.0), "shed": None}[kind]
    if spec is None:
        return wins
    ww, wh, sill, pitch = spec
    for s in range(storeys):
        zb = floor_z + s * sh + sill
        zt = zb + wh
        if s == 0 and shopfront:
            zb, zt = floor_z + 0.35, floor_z + 3.1
            n = max(1, int((L - 0.8) / 3.1))
            w = (L - 0.8) / n
            for k in range(n):
                wins.append((0.4 + k * w + 0.12, 0.4 + (k + 1) * w - 0.12, zb, zt))
            continue
        if zt > eave - 0.25:
            continue
        n = int((L - 1.0) / pitch)
        if n < 1:
            if L > ww + 1.2:
                n = 1
            else:
                continue
        gap = L / n
        for k in range(n):
            c = gap * (k + 0.5)
            wins.append((c - ww / 2, c + ww / 2, zb, zt))
    return wins


def rects_of(ring, cell):
    """The footprint as overlapping rectangles (each in plan: centre, unit axis, half-lengths) whose union is
    the footprint, for a hipped roof per rectangle: their upper envelope is the real roof, valleys and all."""
    P = np.asarray(ring, float)
    E = np.roll(P, -1, 0) - P
    ang = np.arctan2(E[:, 1], E[:, 0]) % (math.pi / 2)
    Ls = np.hypot(E[:, 0], E[:, 1])
    # The dominant direction: length-weighted circular mean of the edge angles modulo 90 degrees.
    th = math.atan2(np.sum(Ls * np.sin(4 * ang)), np.sum(Ls * np.cos(4 * ang))) / 4
    u = np.array([math.cos(th), math.sin(th)])
    v = np.array([-u[1], u[0]])
    Q = np.c_[P @ u, P @ v]
    x0, y0 = Q.min(0)
    x1, y1 = Q.max(0)
    nx, ny = max(1, int(math.ceil((x1 - x0) / cell))), max(1, int(math.ceil((y1 - y0) / cell)))
    from shapely import contains_xy
    from shapely.geometry import Polygon
    pg = Polygon(Q)
    if not pg.is_valid:
        pg = pg.buffer(0)
    gx = x0 + (np.arange(nx) + 0.5) * cell
    gy = y0 + (np.arange(ny) + 0.5) * cell
    GX, GY = np.meshgrid(gx, gy)
    M = contains_xy(pg, GX, GY)
    if M.sum() == 0:
        return []
    cov = np.zeros_like(M)
    out = []
    total = M.sum()
    for _ in range(9):
        unc = M & ~cov
        if unc.sum() <= max(2, 0.04 * total):
            break
        cs = np.cumsum(np.cumsum(unc, 0), 1)
        def usum(i0, i1, j0, j1):
            s = cs[i1, j1]
            if i0 > 0:
                s -= cs[i0 - 1, j1]
            if j0 > 0:
                s -= cs[i1, j0 - 1]
            if i0 > 0 and j0 > 0:
                s += cs[i0 - 1, j0 - 1]
            return s
        best, bsc = None, 0
        for i0 in range(ny):
            acc_row = np.ones(nx, bool)
            for i1 in range(i0, ny):
                acc_row &= M[i1]
                if not acc_row.any():
                    break
                j = 0
                while j < nx:
                    if not acc_row[j]:
                        j += 1
                        continue
                    k = j
                    while k + 1 < nx and acc_row[k + 1]:
                        k += 1
                    h, w = i1 - i0 + 1, k - j + 1
                    if min(h, w) * cell >= 2.0:
                        new = usum(i0, i1, j, k)
                        sc = h * w + 3 * new if new > 0 else 0
                        if sc > bsc:
                            best, bsc = (i0, i1, j, k), sc
                    j = k + 1
        if best is None:
            break
        i0, i1, j, k = best
        cov[i0:i1 + 1, j:k + 1] = True
        cx = x0 + (j + k + 1) / 2 * cell
        cy = y0 + (i0 + i1 + 1) / 2 * cell
        out.append((cx * u + cy * v, u, v, (k - j + 1) * cell / 2, (i1 - i0 + 1) * cell / 2))
    return out


def hip(acc, key, c, u, v, hu, hv, z, pitch, col, over=0.45):
    """A hipped roof on a rectangle, eaves `over` past it, plus its soffit and fascia."""
    hu, hv = hu + over, hv + over
    if hv > hu:
        u, v, hu, hv = v, -u, hv, hu
        u, v = np.asarray(u), np.asarray(v)
    tn = math.tan(math.radians(pitch))
    rise = hv * tn
    c = np.asarray(c, float)
    def P(a, b, zz):
        p = c + u * a + v * b
        return (p[0], p[1], zz)
    e = [P(-hu, -hv, z), P(hu, -hv, z), P(hu, hv, z), P(-hu, hv, z)]
    r0, r1 = P(-(hu - hv), 0, z + rise), P(hu - hv, 0, z + rise)
    lit = lambda f: shade(col, f)
    acc.quad(key, e[0], e[1], r1, r0, lit(1.0))
    acc.quad(key, e[2], e[3], r0, r1, lit(0.92))
    acc.tri(key, e[1], e[2], r1, lit(0.96))
    acc.tri(key, e[3], e[0], r0, lit(0.96))
    acc.quad(key, e[0], e[3], e[2], e[1], SOFFIT)            # the soffit, facing down
    fz = z - 0.2
    f = [P(-hu, -hv, fz), P(hu, -hv, fz), P(hu, hv, fz), P(-hu, hv, fz)]
    for i in range(4):
        acc.quad(key, f[i], f[(i + 1) % 4], e[(i + 1) % 4], e[i], FASCIA)


def flat_roof(acc, key, ring, z, deck, wallcol, big, seed):
    """A flat roof: the deck, a 0.7 m parapet with its cap, and on a big roof the plant and a lift overrun."""
    par = 0.7
    from shapely.geometry import Polygon
    pg = Polygon(ring)
    inner = pg.buffer(-0.3, join_style=2)
    acc.poly(key, [(x, y, z + par) for x, y in ring], shade(wallcol, 1.08)) if inner.is_empty else None
    if inner.is_empty or inner.geom_type != "Polygon":
        return
    ir = ccw_ring([tuple(p) for p in list(inner.exterior.coords)[:-1]])
    acc.poly(key, [(x, y, z) for x, y in ir], deck)
    # Parapet: inner face and cap.
    n = len(ring)
    for i in range(len(ir)):
        a, b = ir[i], ir[(i + 1) % len(ir)]
        acc.quad(key, (b[0], b[1], z), (a[0], a[1], z), (a[0], a[1], z + par), (b[0], b[1], z + par), shade(wallcol, 0.9))
    cap = ccw_ring(ring)
    # The cap as a ring band between the outer and inner outlines (triangulated as the difference).
    import shapely
    band = pg.difference(inner)
    for t in shapely.constrained_delaunay_triangles(band).geoms if band.geom_type == "Polygon" else []:
        cs = list(t.exterior.coords)[:3]
        acc.tri(key, (cs[0][0], cs[0][1], z + par), (cs[1][0], cs[1][1], z + par), (cs[2][0], cs[2][1], z + par),
                shade(wallcol, 1.1))
    if big:
        r = np.random.default_rng(seed)
        mr = inner.minimum_rotated_rectangle
        cs = np.array(mr.exterior.coords)[:4]
        ax = cs[1] - cs[0]
        ay = cs[3] - cs[0]
        for k in range(int(min(4, 1 + inner.area / 300))):
            for _ in range(10):
                fx, fy = r.uniform(0.2, 0.8), r.uniform(0.2, 0.8)
                p = cs[0] + ax * fx + ay * fy
                from shapely.geometry import Point
                if inner.buffer(-2.5).contains(Point(p)):
                    w, d, h = r.uniform(2.0, 4.5), r.uniform(1.6, 3.0), r.uniform(1.2, 2.4)
                    box(acc, key, p, ax / np.linalg.norm(ax), w, d, z, z + h, (168, 170, 170))
                    break
        # A lift overrun on any roof of four storeys or more is the caller's (tall) case.


def box(acc, key, c, u, w, d, z0, z1, col):
    u = np.asarray(u, float)
    v = np.array([-u[1], u[0]])
    c = np.asarray(c, float)
    pts = [c - u * w / 2 - v * d / 2, c + u * w / 2 - v * d / 2, c + u * w / 2 + v * d / 2, c - u * w / 2 + v * d / 2]
    for i in range(4):
        a, b = pts[i], pts[(i + 1) % 4]
        acc.quad(key, (a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1), shade(col, 0.9 + 0.04 * i))
    acc.quad(key, *[(p[0], p[1], z1) for p in pts], col)


def building(acc, b, land, skip_ids):
    if b["id"] in skip_ids:
        return
    ring = simplify(ccw_ring([tuple(p) for p in b["ring"]]))
    if len(ring) < 3:
        return
    P = np.asarray(ring)
    cx, cy = P.mean(0)
    dist = math.hypot(cx - C[0], cy - C[1])
    key = block_of(cx, cy)
    zg = land.z(P[:, 0], P[:, 1])
    floor = float(zg.max()) + (0.35 if b["kind"] in KINDS and KINDS[b["kind"]] == "house" else 0.15)
    base = float(zg.min()) - 0.4
    kind = KINDS.get(b["kind"], None)
    a = b["area"]
    if kind is None:
        kind = "house" if b.get("roof") == "hipped" else "shed" if b.get("roof") == "skillion" else "office"
    if b.get("kind_override"):
        kind = b["kind_override"]
    lv = max(1, int(round(float(b.get("levels", 1)))))
    sh = b.get("storey", STOREY[kind])
    eave = floor + lv * sh
    r = rng.random()
    if kind == "house":
        wcol = pick(WALLS_HOUSE, r)
    elif kind == "flats":
        wcol = pick(WALLS_FLATS, r)
    elif kind == "shed":
        wcol = (176, 172, 164)
    else:
        wcol = pick(WALLS_OFFICE, r)
    if b.get("wall"):
        wcol = tuple(b["wall"])
    roofc = b.get("roof_colour")
    if roofc is None:
        rgb = b.get("roof_rgb")
        if rgb is None:
            roofc = (112, 80, 66)
        else:
            h_, s_, v_ = colorsys.rgb_to_hsv(*[q / 255 for q in rgb])
            if 0.2 < h_ < 0.5 and s_ > 0.1:          # a tree over the roof in the photo: take a tiled roof's colour
                roofc = (128, 78, 62)
            else:
                roofc = dehaze(rgb)
    roof = b.get("roof", "auto")
    if roof == "auto":
        hh, ss, vv = colorsys.rgb_to_hsv(*[q / 255 for q in roofc])
        tiled = ss > 0.3 and (hh < 0.1 or hh > 0.9)
        roof = "hipped" if (tiled and lv <= 6) else "flat"
    shopfront = kind == "retail"
    wins_ok = kind != "shed" and dist < (WIN_R if kind != "house" else 480.0)
    for i in range(len(ring)):
        p0, p1 = ring[i], ring[(i + 1) % len(ring)]
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        wins = window_layout(L, kind, lv, floor, sh, eave, shopfront) if wins_ok else []
        top = eave + (0.7 if roof == "flat" else 0.0)
        wall(acc, (key, "wall"), p0, p1, base, top, wcol, wins, None)
    if roof == "hipped":
        pitch = b.get("pitch", 22.5 if kind == "house" else 24.0)
        cell = 0.75 if a < 400 else 1.5 if a < 1500 else 2.5
        rs = rects_of(ring, cell)
        for c, u, v, hu, hv in rs:
            hip(acc, (key, "roof"), c, u, v, hu, hv, eave, pitch, roofc)
        if not rs:
            acc.poly((key, "roof"), [(x, y, eave) for x, y in ring], roofc)
    elif roof == "skillion":
        acc.poly((key, "roof"), [(x, y, eave + 0.05) for x, y in ring], roofc)
        for i in range(len(ring)):
            p0, p1 = ring[i], ring[(i + 1) % len(ring)]
            acc.quad((key, "roof"), (p0[0], p0[1], eave - 0.15), (p1[0], p1[1], eave - 0.15),
                     (p1[0], p1[1], eave + 0.05), (p0[0], p0[1], eave + 0.05), FASCIA)
    else:
        flat_roof(acc, (key, "roof"), ring, eave, roofc if b.get("roof_rgb") else DECK, wcol, a > 250,
                  abs(hash(b["id"])) % 9999)
        if lv >= 4 and a > 400:
            box(acc, (key, "roof"), (cx, cy), (1, 0), 5.0, 4.0, eave, eave + 3.2, shade(wcol, 0.95))


# ---------------------------------------------------------------- trees
LEAF = {
    "Quercus": (78, 104, 48), "Ulmus": (74, 100, 46), "Platanus": (96, 118, 58), "Fraxinus": (84, 110, 52),
    "Celtis": (82, 106, 54), "Populus": (104, 126, 60), "Zelkova": (84, 108, 50), "Liquidambar": (78, 102, 52),
    "Prunus": (96, 84, 70), "Pyrus": (92, 114, 60), "Acer": (92, 114, 56), "Gleditsia": (118, 132, 62),
    "Robinia": (112, 128, 62), "Brachychiton": (56, 82, 42), "Eucalyptus": (104, 114, 84), "Cedrus": (62, 82, 70),
    "Pinus": (56, 76, 50), "Cupressus": (48, 66, 44), "Calocedrus": (52, 72, 48), "Casuarina": (88, 96, 72),
    "Callistemon": (82, 96, 60), "Ilex": (52, 72, 44), "Alnus": (74, 98, 50), "Malus": (92, 110, 58),
    "Crataegus": (84, 104, 56), "Lagerstroemia": (90, 110, 60), "Ginkgo": (112, 132, 66),
}
# Crown profiles: (height fraction of the crown, radius fraction) from the crown's base up.
ROUND = [(0.0, 0.6), (0.3, 0.97), (0.7, 0.88), (1.0, 0.2)]
GUM = [(0.0, 0.5), (0.4, 1.0), (0.8, 0.8), (1.0, 0.3)]
CONE = [(0.0, 1.0), (0.4, 0.68), (0.8, 0.26), (1.0, 0.02)]
COLUMN = [(0.0, 0.6), (0.15, 1.0), (0.7, 0.85), (1.0, 0.05)]
PINE = [(0.0, 0.7), (0.3, 1.0), (0.7, 0.9), (1.0, 0.35)]


def tree_shape(t):
    g = t["genus"]
    h, r = t["h"], t["r"]
    slim = r / max(h, 1.0)
    if g in ("Cupressus", "Calocedrus") or (g is None and slim < 0.17 and h > 7):
        return COLUMN, 0.06, LEAF["Cupressus"], (70, 56, 44)
    if g == "Populus" and slim < 0.26:
        return COLUMN, 0.12, LEAF["Populus"], (150, 146, 132)
    if g == "Cedrus":
        return CONE, 0.08, LEAF["Cedrus"], (82, 64, 50)
    if g == "Pinus":
        return PINE, 0.45, LEAF["Pinus"], (92, 66, 50)
    if g == "Eucalyptus" or (g is None and rng.random() < 0.28):
        return GUM, 0.42, LEAF["Eucalyptus"], (214, 206, 190)
    col = LEAF.get(g) or [LEAF["Quercus"], LEAF["Ulmus"], LEAF["Fraxinus"], LEAF["Prunus"], LEAF["Platanus"],
                          LEAF["Liquidambar"]][int(rng.integers(6))]
    return ROUND, 0.3, col, (96, 82, 66)


def crown_outline(t, n=7):
    """The LiDAR crown's outline sampled at n bearings round its centre (radii from the polygon)."""
    ring = np.asarray(t["ring"], float)
    c = np.array([t["x"], t["y"]])
    q = ring - c
    ang = np.arctan2(q[:, 1], q[:, 0])
    rad = np.hypot(q[:, 0], q[:, 1])
    o = np.argsort(ang)
    bs = np.linspace(-math.pi, math.pi, n, endpoint=False) + rng.uniform(0, 2 * math.pi / n)
    bs = (bs + math.pi) % (2 * math.pi) - math.pi
    rr = np.interp(bs, ang[o], rad[o], period=2 * math.pi)
    rr = np.clip(rr, 0.6 * t["r"], 1.5 * t["r"])
    return bs, rr


def tree(acc, t, land):
    prof, base_f, leaf, bark = tree_shape(t)
    zb = float(land.z(t["x"], t["y"]))
    h = max(3.0, t["h"])
    key = block_of(t["x"], t["y"])
    bs, rr = crown_outline(t, 7 if math.hypot(t["x"] - C[0], t["y"] - C[1]) < 300 else 6 if math.hypot(t["x"] - C[0], t["y"] - C[1]) < 650 else 5)
    if prof is COLUMN:
        rr = np.minimum(rr, max(1.0, 0.16 * h) if t["genus"] != "Populus" else 0.24 * h)
    cb = zb + h * base_f
    ch = zb + h - cb
    vary = 0.66 + 0.2 * rng.random()    # lit by the match's sun: darker than the register's leaf to read as Google Earth's
    lc = shade(leaf, vary)
    dist = math.hypot(t["x"] - C[0], t["y"] - C[1])
    if dist < NEAR_TREES and prof in (ROUND, GUM):
        lobed_crown(acc, key, t, bs, rr, cb, ch, lc, prof is GUM)
        trunk(acc, key, t, zb, h, cb, ch, bark)
        return
    n = len(bs)
    V, cols = [], []
    for k, (f, s) in enumerate(prof):
        jit = 1.0 + rng.uniform(-0.14, 0.14, n)
        zz = cb + ch * f
        up = 0.8 + 0.34 * (k / (len(prof) - 1))
        for b, r, j in zip(bs, rr, jit):
            V.append((t["x"] + math.cos(b) * r * s * j, t["y"] + math.sin(b) * r * s * j, zz + rng.uniform(-0.04, 0.04) * ch))
            cols.append(shade(lc, up * rng.uniform(0.92, 1.06)))
    top = len(V)
    V.append((t["x"], t["y"], cb + ch * 1.03))
    cols.append(shade(lc, 1.14))
    bot = len(V)
    V.append((t["x"], t["y"], cb - 0.1))
    cols.append(shade(lc, 0.6))
    F = []
    nr = len(prof)
    for k in range(nr - 1):
        for i in range(n):
            a0, a1 = k * n + i, k * n + (i + 1) % n
            b0, b1 = a0 + n, a1 + n
            F += [(a0, a1, b1), (a0, b1, b0)]
    for i in range(n):
        F.append(((nr - 1) * n + i, (nr - 1) * n + (i + 1) % n, top))
        F.append(((i + 1) % n, i, bot))
    acc.mesh((key, "leaf"), V, F, cols)
    trunk(acc, key, t, zb, h, cb, ch, bark)


NEAR_TREES = 260.0     # the trees seen from the stands: crowns built of lobes, as Google Earth's canopy reads


def lobed_crown(acc, key, t, bs, rr, cb, ch, lc, gum):
    """A broadleaf crown as a cluster of leafy lobes inside the LiDAR outline: a central mass and 3 to 6 lobes
    round it, each an eight-sided ellipsoid, lit lighter on top and darker beneath."""
    r = float(np.mean(rr))
    nl = int(np.clip(round(r / 2.0), 3, 6))
    lobes = [(t["x"], t["y"], cb + ch * 0.5, 0.62 * r, 0.5 * ch)]
    for i in range(nl):
        a = bs[0] + 2 * math.pi * (i + rng.uniform(-0.25, 0.25)) / nl
        rad = float(np.interp(a, bs, rr, period=2 * math.pi))
        d = rad * rng.uniform(0.4, 0.55)
        zc = cb + ch * rng.uniform(0.38, 0.62 if not gum else 0.72)
        lr = rad * rng.uniform(0.45, 0.6)
        lobes.append((t["x"] + math.cos(a) * d, t["y"] + math.sin(a) * d, zc, lr, ch * rng.uniform(0.3, 0.42)))
    lat = [-80, -45, -10, 25, 60]
    n = 8
    for (x, y, z, lr, lz) in lobes:
        V, cols = [], []
        sh = rng.uniform(0.9, 1.08)
        for la in lat:
            cl, sl = math.cos(math.radians(la)), math.sin(math.radians(la))
            jit = 1.0 + rng.uniform(-0.16, 0.16, n)
            off = rng.uniform(0, 2 * math.pi)
            for i in range(n):
                b = off * 0.15 + 2 * math.pi * i / n
                V.append((x + math.cos(b) * lr * cl * jit[i], y + math.sin(b) * lr * cl * jit[i], z + lz * sl))
                cols.append(shade(lc, sh * (0.7 + 0.42 * (sl + 1) / 2) * rng.uniform(0.94, 1.05)))
        top = len(V); V.append((x, y, z + lz * 1.02)); cols.append(shade(lc, sh * 1.14))
        bot = len(V); V.append((x, y, z - lz)); cols.append(shade(lc, sh * 0.62))
        F = []
        for k in range(len(lat) - 1):
            for i in range(n):
                a0, a1 = k * n + i, k * n + (i + 1) % n
                F += [(a0, a1, a1 + n), (a0, a1 + n, a0 + n)]
        k = len(lat) - 1
        for i in range(n):
            F.append((k * n + i, k * n + (i + 1) % n, top))
            F.append(((i + 1) % n, i, bot))
        acc.mesh((key, "leaf"), V, F, cols)


def trunk(acc, key, t, zb, h, cb, ch, bark):
    """A tapered three-sided stem up into the crown."""
    tr = max(0.12, h / 70.0)
    zt = cb + ch * 0.35
    for i in range(3):
        a0, a1 = 2 * math.pi * i / 3, 2 * math.pi * (i + 1) / 3
        p = lambda a, rad, z: (t["x"] + math.cos(a) * rad, t["y"] + math.sin(a) * rad, z)
        acc.quad((key, "bark"), p(a0, tr, zb - 0.2), p(a1, tr, zb - 0.2), p(a1, tr * 0.55, zt), p(a0, tr * 0.55, zt),
                 shade(bark, 0.85 + 0.1 * math.cos(a0)))


# ---------------------------------------------------------------- export
MATS = {"wall": (0.9, 0.0), "roof": (0.75, 0.0), "leaf": (1.0, 0.0), "bark": (1.0, 0.0)}


def export(acc, gnd, path, extra=None):
    import trimesh
    from PIL import Image
    sc = trimesh.Scene()
    def to_gl(P):
        P = np.asarray(P, float)
        return np.c_[P[..., 0], P[..., 2], -P[..., 1]]

    def add(m, C4, mat, blk, tag=""):
        rough, metal = MATS[mat]
        m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=C4)
        name = "town_%s%s_%d_%d" % (mat, tag, blk[0], blk[1])
        m.visual.material = trimesh.visual.material.PBRMaterial(name="town_" + mat, baseColorFactor=[255, 255, 255, 255],
                                                                roughnessFactor=rough, metallicFactor=metal,
                                                                doubleSided=True)
        sc.add_geometry(m, node_name=name, geom_name=name)
    for (blk, mat), (tris, cols) in sorted(acc.parts.items(), key=lambda kv: str(kv[0])):
        T = np.asarray(tris, float).reshape(-1, 3, 3)
        fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-9)
        col = np.asarray(cols, float)
        rows = np.concatenate([T.reshape(-1, 3), np.repeat(fn, 3, 0), np.repeat(col, 3, 0)], 1)
        key = np.round(rows, 3)
        uq, inv = np.unique(key, axis=0, return_inverse=True)
        V = to_gl(uq[:, :3])
        N = to_gl(uq[:, 3:6])
        F = inv.reshape(-1, 3)      # (x, y, z) -> (x, z, -y) is a rotation: the winding stands
        C4 = np.c_[uq[:, 6:9], np.full(len(uq), 255.0)].astype(np.uint8)
        m = trimesh.Trimesh(V, F, vertex_normals=N, process=False)
        add(m, C4, mat, blk)
    for (blk, mat), (Vs, Fs, Cs) in sorted(acc.smooth.items(), key=lambda kv: str(kv[0])):
        V = to_gl(np.concatenate(Vs))
        F = np.concatenate(Fs)
        col = np.concatenate(Cs)
        m = trimesh.Trimesh(V, F, process=False)
        m.vertex_normals    # smooth normals from the faces
        add(m, np.c_[col, np.full(len(col), 255.0)].astype(np.uint8), mat, blk, "s")
    if gnd is not None:
        V = to_gl(gnd["v"])
        F = gnd["f"]
        jp = os.path.join(CACHE, "groundmap.jpg")
        Image.open(os.path.join(CACHE, "groundmap.png")).convert("RGB").save(jp, quality=90)
        img = Image.open(jp)        # kept as JPEG inside the glb
        mat = trimesh.visual.material.PBRMaterial(name="town_ground", baseColorTexture=img, roughnessFactor=1.0,
                                                  metallicFactor=0.0)
        uv = np.c_[gnd["uv"][:, 0], 1 - gnd["uv"][:, 1]]
        g = trimesh.Trimesh(V, F, process=False, visual=trimesh.visual.TextureVisuals(uv=uv, material=mat))
        sc.add_geometry(g, node_name="town_ground", geom_name="town_ground")
    if extra:
        for name, m in extra:
            sc.add_geometry(m, node_name=name, geom_name=name)
    sc.export(path, include_normals=True)


def main():
    data = json.load(open(os.path.join(CACHE, "town.json")))
    dem = ground_heights()
    rad = apron_r()
    land = Land(dem, rad)
    gnd = {}
    ground(gnd, dem, rad)
    acc = Acc()
    lm = None
    skip = set()
    try:
        import landmarks
        skip = set(landmarks.REPLACES)
        lm = landmarks
    except ImportError:
        pass
    nb = 0
    if lm:
        lm.apply_overrides(data["buildings"])
    for b in data["buildings"]:
        building(acc, b, land, skip)
        nb += 1
    for t in data["trees"]:
        tree(acc, t, land)
    if lm:
        lm.build(acc, land, data["buildings"])
    ntri = sum(len(v[0]) for v in acc.parts.values()) + sum(sum(len(f) for f in v[1]) for v in acc.smooth.values())
    out = os.path.join(ASSETS, "manuka_backdrop_part1.glb")
    export(acc, gnd, out)
    print("buildings", nb, "trees", len(data["trees"]), "triangles", ntri + len(gnd["f"]), "->", out,
          "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
