"""Traeger Park's near scene: the ground, buildings and gums from the stadium out to R_OUT (1,300 m).

    python3 near.py OUT.glb [MOSAIC.png]

- The ground: rings round the oval (720 bearings, as far.py's, so the two meet on the same ring), flat under
  the stadium and following the real heights from 350 m out (Billy Goat Hill to the east, the rise to the
  ranges), painted by paint.py: an inner map 500 m a side at 0.24 m a pixel round the stadium and an outer
  map 2.6 km a side at 1.27 m.
- Buildings: every OpenStreetMap footprint outside the stadium model, and Microsoft's footprints for the
  ~500 that OpenStreetMap lacks (bldg.py), each roof in its colour off
  Google Earth's straight-down views (MOSAIC: the mosaic of them, 0.5 m a pixel, see qa/README).
- Gums: every canopy in those views (canopy.py) stood up as a tree (trees.py).

Model metres (x east, y up, z south), the field's level at 0. Looks only. Map data (c) OpenStreetMap
contributors (ODbL); Microsoft Global ML Building Footprints (ODbL); Contains modified Copernicus Sentinel
data 2025. Needs shapely.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

import bldg
import canopy
import far
import geo
import glb
import paint
import surface
import trees as T

R_OUT = far.R_IN
NB = far.NB
FLAT_R, HILL_R = 350.0, 700.0
GROUND_Y = -0.12            # just under the model's own floor (FIT -0.05)
INNER = 250.0
MID = 650.0
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "traeger", "traeger.glb")


class Land:
    def __init__(self, dem, h0):
        self.dem, self.h0 = dem, h0

    def y(self, e, n):
        r = np.hypot(e, n)
        t = np.clip((r - FLAT_R) / (HILL_R - FLAT_R), 0, 1)
        t = t * t * (3 - 2 * t)
        return GROUND_Y + t * (self.dem.at(e, n) - self.h0) - r ** 2 / (2 * far.EARTH_R)


def thin(tl):
    """Past the near gums, a card stands for a stand of trees: the biggest crown in each 7 m (to 700 m) or
    11 m (beyond) keeps its place, the smaller ones round it go. From the broadcast cameras those gums are a
    line of canopy over the roofs, and the cards still close the gaps (each is a whole crown wide)."""
    keep, cell = [], {}
    for t in sorted(tl, key=lambda t: -t[3]):
        e, n, h, rad = t
        r = math.hypot(e, n)
        sp = 0.0 if r < T.MID_R else (7.0 if r < 700 else 11.0)
        if sp:
            cx, cy = int(e // 11), int(n // 11)
            near_ = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cy + j), [])]
            if any(math.hypot(q[0] - e, q[1] - n) < sp for q in near_):
                continue
            cell.setdefault((cx, cy), []).append((e, n))
        keep.append(t)
    return keep


def model_mask():
    """Where the stadium model stands (east/north), so OpenStreetMap's own outlines of its stands,
    clubrooms and sheds are not built twice: every triangle of the model from 1 m to 30 m up, filled
    top-down onto a 1 m grid over +-250 m (row = z + 250, column = x + 250)."""
    import cv2
    import trimesh
    sc = trimesh.load(MODEL)
    m = np.zeros((500, 500), np.uint8)
    for name, g in sc.geometry.items():
        if name.startswith("ground") or name.startswith("fence"):
            continue
        v = g.vertices
        f = g.faces[(v[g.faces][:, :, 1].max(1) > 1.0) & (v[g.faces][:, :, 1].min(1) < 30.0)]
        tri = np.stack([v[f][:, :, 0] + 250, v[f][:, :, 2] + 250], -1)
        for t in np.round(tri).astype(np.int32):
            cv2.fillConvexPoly(m, t, 1)
    from scipy import ndimage
    return ndimage.binary_dilation(m > 0, iterations=2)


# The match fit (GroundModels.FIT traeger): field centre x, z, floor, long axis deg, half length, half width.
FIT = (3.62, -8.97, -0.05, -90.9, 93.26, 73.2)


def on_field(e, n, margin=6.0):
    """Inside the playing surface's ellipse, or within margin of its edge (no gum there)."""
    cx, cz, _, ang, hl, hw = FIT
    a = math.radians(ang)
    dx, dz = e - cx, -n - cz
    rx = dx * math.cos(a) + dz * math.sin(a)
    rz = -dx * math.sin(a) + dz * math.cos(a)
    return (rx / (hl + margin)) ** 2 + (rz / (hw + margin)) ** 2 < 1.0


def in_model(mask, p):
    """A footprint (or a point) a third or more of which lies on the model."""
    from PIL import Image, ImageDraw
    if len(p) == 1:
        i, j = int(-p[0][1] + 250), int(p[0][0] + 250)
        return 0 <= i < 500 and 0 <= j < 500 and bool(mask[i, j])
    im = Image.new("L", (500, 500), 0)
    ImageDraw.Draw(im).polygon([(e + 250, -n + 250) for e, n in p], fill=1)
    a = np.asarray(im, bool)
    if a.sum() == 0:
        return False
    return (a & mask).sum() >= a.sum() / 3


def ground(land, maps):
    """The ground as rings of points round the oval. The outermost band has far.py's 720 bearings so the two
    meet on the same ring; each band inwards halves the bearings (their spacing stays near 2-5 m), joined to
    the next by a ring of fan triangles."""
    rr = [20.0]
    while rr[-1] < R_OUT:
        rr.append(min(R_OUT, rr[-1] + max(3.0, rr[-1] * 0.02)))
    rr = np.array(rr)
    nb = np.where(rr > 600, NB, np.where(rr > 300, NB // 2, np.where(rr > 140, NB // 4, NB // 8)))
    P = []
    for r, k in zip(rr, nb):
        bb = np.radians(np.arange(k) * 360.0 / k)
        E, N = r * np.sin(bb), r * np.cos(bb)
        P.append(np.stack([E, land.y(E, N), -N], -1))
    starts = np.cumsum([0] + [len(x) for x in P])[:-1]
    P = np.concatenate(P)
    F = []
    for i in range(len(rr) - 1):
        a0, ka = starts[i], nb[i]
        b0, kb = starts[i + 1], nb[i + 1]
        if ka == kb:
            j = np.arange(ka)
            a, a1 = a0 + j, a0 + (j + 1) % ka
            c, c1 = b0 + j, b0 + (j + 1) % kb
            F.append(np.stack([a, c, a1], -1))
            F.append(np.stack([a1, c, c1], -1))
        else:                                   # kb == 2 ka: each inner edge fans to two outer edges
            j = np.arange(ka)
            a, a1 = a0 + j, a0 + (j + 1) % ka
            c, cm, c1 = b0 + 2 * j, b0 + 2 * j + 1, b0 + (2 * j + 2) % kb
            F.append(np.stack([a, c, cm], -1))
            F.append(np.stack([a, cm, a1], -1))
            F.append(np.stack([a1, cm, c1], -1))
    F = np.concatenate(F)
    # centre disc
    Nrm = glb.grid_normals(P, F)
    if Nrm[:, 1].mean() < 0:
        F = F[:, ::-1]
        Nrm = -Nrm
    e, n = P[:, 0], -P[:, 2]
    out = []
    for name, cv in maps:
        uv = np.stack([(e - cv.cx + cv.r) / (2 * cv.r), (cv.r - (n - cv.cy)) / (2 * cv.r)], -1)
        inside = (np.abs(e - cv.cx) <= cv.r) & (np.abs(n - cv.cy) <= cv.r)
        out.append((name, uv, inside))
    # each triangle to the finest map that holds all three corners
    fi = np.zeros(len(F), int) - 1
    for k, (name, uv, inside) in enumerate(out):
        allin = inside[F].all(1) & (fi < 0)
        fi[allin] = k
    fi[fi < 0] = len(out) - 1
    return P, Nrm, F, fi, out


def main(path, mosaic):
    dem = geo.Dem(far.R_OUT + 500)
    h0 = far.field_asl(dem)
    land = Land(dem, h0)
    nodes, ways = geo.osm(R_OUT + 100)
    mm = model_mask()
    mos = canopy.Mosaic(mosaic) if mosaic else None
    # buildings outside the model
    blds = []
    for wid, t, p in ways:
        if "building" not in t or len(p) < 4 or t.get("layer", "0").startswith("-"):
            continue
        c = np.mean(p, 0)
        r = math.hypot(*c)
        if r > R_OUT - 20 or in_model(mm, p):
            continue
        blds.append((wid, t, p, r))
    blds += _ms_extra(blds, mm)
    # trees
    if mos:
        roofm = surface.roof_mask(mos, [(t, p, wid) for wid, t, p, _ in blds], _storeys)
        can = surface.canopy_mask(mos.a, roofm)
        tl = mos.trees(can, lambda e, n: in_model(mm, [(e, n)]) or on_field(e, n), geo.Chm())
        tl = thin(tl)
    else:
        tl = []
    print("buildings", len(blds), "trees", len(tl))
    # maps: the surfaces traced off the mosaic (surface.py), or without one OpenStreetMap over Sentinel-2
    maps = []
    canv = (("ground_inner", paint.Canvas(INNER, 2048)), ("ground_mid", paint.Canvas(MID, 2048)),
            ("ground_outer", paint.Canvas(R_OUT, 2048)))
    surf = surface.Surfaces(mos, roofm, can) if mos else None
    for name, cv in canv:
        if surf:
            img = surf.paint(cv)
            img = paint.lane_lines(cv, img, ways)
        else:
            img, _ = paint.base_colour(cv, [(t, p) for _, t, p, _ in blds])
            img = paint.draw_world(cv, img, ways, extra=lambda cv_, d, im: _slabs(cv_, d, blds))
        img = paint.shade(cv, img, [(e, n, h, rad) for e, n, h, rad in tl])
        maps.append((name, cv, Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))))
    P, Nrm, F, fi, uvs = ground(land, [(n_, cv) for n_, cv, _ in maps])
    w = glb.Glb()
    for k, (name, cv, im) in enumerate(maps):
        sel = F[fi == k]
        used = np.unique(sel)
        remap = np.full(len(P), -1)
        remap[used] = np.arange(len(used))
        im.save(os.path.join(os.path.dirname(path), name + ".jpg"), quality=90)
        m = w.material(name, image=glb.jpeg(im, 90))
        w.mesh(name, P[used], Nrm[used], remap[sel], m, uv=uvs[k][1][used],
               col=np.full((len(used), 4), 255, np.uint8))
    # buildings
    B = bldg.Builder()
    rng = np.random.default_rng(5)
    for wid, t, p, r in blds:
        y0 = float(land.y(*np.mean(p, 0)))
        roof = mos.roof_colour(p, 4.0) if mos else (190, 188, 182)
        wall, mat = _wall(rng)
        kind = t.get("building")
        storeys = _storeys(t, p, wid)
        B.add(p, y0, kind, tuple(int(c) for c in roof) + (255,), wall, mat, storeys=storeys, r=r)
    tex = os.path.join(HERE, "tex")
    mats = {"facade_brick": ("brick.png", "image/png"), "facade_render": ("render.png", "image/png"),
            "roof_corr": ("corrugated.png", "image/png")}
    for name, b in list(B.walls.items()) + [("roof_corr", B.roof)]:
        Pb, Nb, Fb, UVb, Cb = b.arrays()
        if len(Fb):
            f, mime = mats[name]
            m = w.material(name, image=open(os.path.join(tex, f), "rb").read(), mime=mime, double=True)
            w.mesh(name, Pb, Nb, Fb, m, uv=UVb / (1.52 if name == "roof_corr" else 1.2), col=Cb)
    for name, b, kw in (("trim", B.trim, {}), ("window_glass", B.glass, {"rough": 0.15})):
        Pb, Nb, Fb, UVb, Cb = b.arrays()
        if len(Fb):
            m = w.material(name, colour=(1, 1, 1, 1) if name == "trim" else (0.16, 0.19, 0.22, 1), double=True, **kw)
            w.mesh(name, Pb, Nb, Fb, m, col=Cb if name == "trim" else None)
    # gums
    Fo = T.Forest()
    for k, (e, n, h, rad) in enumerate(tl):
        Fo.add(e, n, float(land.y(e, n)), h, rad, k * 7 + 3, math.hypot(e, n))
    leaf = os.path.join(tex, "leaves.png")
    Pl, Nl, Fl, UVl, Cl = Fo.leaf.arrays()
    if len(Fl):
        w.mesh("gum_leaf", Pl, Nl, Fl, w.material("gum_leaf", image=open(leaf, "rb").read(), mime="image/png",
                                                  double=False, alpha_cut=0.5), uv=UVl, col=Cl)
        Pb, Nb, Fb, UVb, Cb = Fo.bark.arrays()
        w.mesh("gum_bark", Pb, Nb, Fb, w.material("gum_bark"), col=Cb)
    Pf, Nf, Ff, UVf, Cf = Fo.far.arrays()
    if len(Ff):
        w.mesh("gum_far", Pf, Nf, Ff, w.material("gum_far", image=open(os.path.join(tex, "gum_far.png"), "rb").read(),
                                                 mime="image/png", alpha_cut=0.5), uv=UVf, col=Cf)
    w.save(path)
    tris = len(F) + sum(len(b.F) for b in list(B.walls.values()) + [B.roof, B.trim, B.glass]) + len(Fo.leaf.F) + len(Fo.bark.F) + len(Fo.far.F)
    print("near", path, "buildings", B.count, "trees", Fo.n, "triangles", tris)


def _ms_extra(blds, mm):
    """The buildings OpenStreetMap lacks (some 500 houses, sheds and carports round the ground): Microsoft's
    footprints (geo.ms_buildings) that no OpenStreetMap building already covers by a third or more."""
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree
    have = [Polygon(p).buffer(0) for _, _, p, _ in blds]
    tree = STRtree(have)
    out = []
    for k, p in enumerate(geo.ms_buildings(R_OUT)):
        g = Polygon(p).buffer(0)
        c = np.mean(p, 0)
        r = math.hypot(*c)
        if r > R_OUT - 20 or g.area < 6.0 or in_model(mm, p) or on_field(*c):
            continue
        if sum(g.intersection(have[i]).area for i in tree.query(g)) >= g.area / 3:
            continue
        out.append(("ms%d" % k, {"building": "yes"}, p, r))
    print("buildings from Microsoft's footprints:", len(out))
    return out


def _slabs(cv, d, blds):
    for _, t, p, _ in blds:
        d.polygon(cv.pts(p), fill=paint.SLAB)


WALLS = [((206, 190, 160, 255), "facade_brick", 0.28), ((226, 220, 204, 255), "facade_render", 0.30),
         ((150, 96, 74, 255), "facade_brick", 0.14), ((196, 198, 194, 255), "facade_render", 0.12),
         ((214, 196, 150, 255), "facade_render", 0.10), ((176, 150, 120, 255), "facade_brick", 0.06)]


def _wall(rng):
    k = rng.random()
    acc = 0.0
    for col, mat, p in WALLS:
        acc += p
        if k < acc:
            j = rng.uniform(0.94, 1.04)
            return tuple(int(min(255, c * j)) for c in col[:3]) + (255,), mat
    return WALLS[0][0], WALLS[0][1]


# Storeys counted off Google Earth's oblique views (qa/obl.json), by OpenStreetMap way id: the hospital
# (3-storey main block with its fins, 2-storey wings, the 3-storey staff blocks north of it), the town
# centre (Yeperenye and Alice Plaza with roof car parks, the police station), the convention centre and the
# hotels by the casino. Every other building in reach is single storey (Google Earth's orbits, qa/views.json).
STOREYS = {"311434565": 3, "311434155": 2, "311434564": 2, "r4169290_311433979": 2, "311434568": 3,
           "884874912": 3, "311434569": 2,
           "257906785": 2, "93084668": 2, "257906829": 2, "257906841": 2, "309760854": 2, "173091683": 2,
           "257906842": 2,
           "311117645": 2, "310975959": 2, "311118177": 2, "r4164103_311118661": 2}


def _storeys(t, p, wid=None):
    if wid in STOREYS:
        return STOREYS[wid]
    if t.get("building:levels"):
        try:
            return max(1, int(float(t["building:levels"])))
        except ValueError:
            pass
    return 1


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
