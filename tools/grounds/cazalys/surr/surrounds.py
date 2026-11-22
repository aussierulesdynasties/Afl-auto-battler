"""Cazaly's Stadium's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Westcourt and Parramatta Park round the ground, 2 km a side at 1 m a pixel: Mulgrave Road and the
streets, the car yards and sheds along Mulgrave Road, the houses (Queenslanders and low-set brick under
iron roofs), Chinaman Creek and Moody Creek with the scrub along their banks, Dillon Street Reserve and the
other parks. It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with Cairns's colours, as
Bellerive's and GMHBA's do, and stands every mapped building and tree up.

    python3 tools/grounds/cazalys/surr/surrounds.py <osm dir> <chm.tif>

<osm dir> holds the tiles osm_fetch.py wrote (`osm_fetch.py <dir> 1200 800`). <chm.tif> is Meta and WRI's
global canopy height map tile 311023111 (CC BY 4.0, dataforgood-fb-data/forests/v1/alsgedi_global_v6_float/chm):
the canopy over 3.5 m in it is covered with crowns where it grows, each at its height. Writes
assets/grounds/cazalys/surrounds.webp, trees.bin and buildings.bin (the MCG's formats), in model metres:
x east, z south, the model's origin (the OSM pitch's centroid, model/../work/geo.py) at 0, 0.
Map data (c) OpenStreetMap contributors, ODbL. Canopy heights (c) Meta and World Resources Institute, CC BY 4.0.
No aerial imagery is used.
"""
import glob
import importlib.util
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mcg_surrounds", os.path.join(HERE, "..", "..", "mcg", "surrounds.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

OUT = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "cazalys")
GLB = os.path.join(OUT, "cazalys.glb")
S.LAT0, S.LON0 = -16.935653, 145.749062
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Google Earth over Westcourt (2026-11-22): green wet-season couch on the reserves, grey-green house blocks
# (iron roofs among mango and fig canopies), dark olive creek scrub, brown-green creek water.
S.BASE = (106, 114, 72)
S.LAWN = (100, 118, 64)
S.PITCH = (94, 116, 60)
S.URBAN = (112, 116, 98)
S.PARKING = (96, 96, 96)
S.ASPHALT = (78, 78, 80)
S.PAVED = (150, 146, 136)
S.ROOF = (150, 150, 146)
S.WATER = (78, 84, 62)
S.WOOD = (60, 80, 46)
CREEK_W = {"river": 14.0, "stream": 9.0, "drain": 5.0, "ditch": 3.0, "canal": 10.0}
CREEK_BANK = 14.0                 # scrub and trees each side of the creek channels (Google Earth)


def footprint():
    """The stadium's plan as a 1 m mask in the map's pixels: the model draws it."""
    import trimesh
    sc = trimesh.load(GLB)
    v = sc.to_geometry().vertices if hasattr(sc, "to_geometry") else sc.dump(concatenate=True).vertices
    v = v[v[:, 1] > 0.5]
    v = v[np.hypot(v[:, 0], v[:, 2]) < 175.0]
    m = np.zeros((S.SIZE, S.SIZE), bool)
    ix = np.clip((v[:, 0] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    iz = np.clip((v[:, 2] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    m[iz, ix] = True
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0


def creeks(ways):
    """Creek channels (water) and their wooded banks as 1 m masks."""
    wat = Image.new("L", (S.SIZE, S.SIZE), 0)
    bank = Image.new("L", (S.SIZE, S.SIZE), 0)
    dw, db = ImageDraw.Draw(wat), ImageDraw.Draw(bank)
    for t, p in ways:
        w = CREEK_W.get(t.get("waterway"))
        if w and len(p) > 1 and t.get("tunnel") not in ("culvert", "yes"):
            pts = [S.px(*q) for q in p]
            db.line(pts, fill=255, width=int(w + 2 * CREEK_BANK))
            dw.line(pts, fill=255, width=int(w))
    return np.asarray(wat) > 0, np.asarray(bank) > 0


def chm_trees(path, block):
    """(x, z, height, crown radius) of the crowns covering the canopy height map's canopy within 1,000 m."""
    import rasterio
    from rasterio.windows import from_bounds
    from scipy import ndimage
    r = rasterio.open(path)
    R = 6378137.0
    mx = math.radians(S.LON0) * R
    my = R * math.log(math.tan(math.pi / 4 + math.radians(S.LAT0) / 2))
    k = 1 / math.cos(math.radians(S.LAT0))              # Web Mercator's stretch here
    half = 1050 * k
    a = r.read(1, window=from_bounds(mx - half, my - half, mx + half, my + half, r.transform)).astype(float)
    step = r.transform.a / k                            # ground metres a pixel
    sm = ndimage.gaussian_filter(a, 0.7)
    can = sm >= 3.5
    # Each canopy pixel inside a crown's reach is covered; the tallest uncovered pixel gets the next crown,
    # its radius from its height (Cairns's mangoes, figs and raintrees are about 0.35 of their height across).
    ys, xs = np.nonzero(can)
    order = np.argsort(-sm[ys, xs], kind="stable")
    cell, out = {}, []
    for o in order:
        y, x = ys[o], xs[o]
        X = (x - a.shape[1] / 2 + 0.5) * step
        Z = (y - a.shape[0] / 2 + 0.5) * step               # rows run south
        if abs(X) > 1000 or abs(Z) > 1000:
            continue
        h = float(sm[y, x])
        rad = float(np.clip(0.36 * h + 0.8, 2.2, 7.5))
        cx, cz = int(X // 8), int(Z // 8)
        if any(math.hypot(q[0] - X, q[1] - Z) < 0.75 * (rad + q[3]) for i in (-1, 0, 1) for j in (-1, 0, 1)
               for q in cell.get((cx + i, cz + j), [])):
            continue
        q = (X, Z, h, rad)
        cell.setdefault((cx, cz), []).append(q)
        if not block(X, Z):
            out.append(q)
    return out


def building_list(ways, in_foot):
    """Houses (mapped as house / detached / yes under 300 m2) get walls and a hipped iron roof (negative
    height): Westcourt's Queenslanders stand on stumps, so their eaves sit at 5 m, the low-set brick ones
    at 3 m. Sheds and shops along Mulgrave Road keep their flat roofs at the tagged or usual height."""
    out = []
    rng = np.random.default_rng(41)
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        pts = [S.model_xz(*q) for q in p[:-1]]
        if in_foot(p) or max(max(abs(x), abs(z)) for x, z in pts) > 1000:
            continue
        h = S.building_height(t)
        if h < 2.5:
            continue
        a = abs(S._area(np.array(pts + pts[:1])))
        if "height" not in t and t.get("building") in ("house", "detached", "semidetached_house", "bungalow", "yes",
                                                        "residential") and a < 300.0:
            lv = t.get("building:levels")
            if lv not in (None, "1"):
                h = -(float(lv) * 3.0)
            else:
                h = -(5.0 if rng.random() < 0.55 else 3.0)
        elif t.get("building") in ("garage", "shed", "carport"):
            h = 2.8
        elif "height" not in t and "building:levels" not in t and a >= 300.0:
            h = 6.5 if t.get("building") in ("industrial", "warehouse", "retail", "commercial", "yes") else h
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    return np.array(out, "<f4")


def main():
    paths = sorted(glob.glob(os.path.join(sys.argv[1], "*.osm")))
    trees, ways, seen = [], [], set()
    for p in paths:
        t, w = S.load(p)
        for e in t:
            if e not in seen:
                seen.add(e); trees.append(e)
        ways += w
    # The tiles overlap at their edges: one copy of each way.
    uniq, keys = [], set()
    for t, p in ways:
        k = (tuple(sorted(t.items())), tuple(p[:2]), len(p))
        if k not in keys:
            keys.add(k); uniq.append((t, p))
    ways = uniq
    foot = footprint()

    def in_foot(pts):
        return any(foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                   for x, z in (S.model_xz(*q) for q in pts))

    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch"))
                                            and len(p) > 2 and in_foot(p))]
    for t, p in ways:
        if t.get("leisure") == "nature_reserve" or t.get("natural") == "wood":
            t.setdefault("leisure", "park")
    trees = [e for e in trees if not in_foot([e]) and max(abs(c) for c in S.model_xz(*e)) < 1000]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).astype(float)
    wat, bank = creeks(ways)
    rng = np.random.default_rng(5)
    n1 = np.asarray(Image.fromarray((rng.random((256, 256)) * 255).astype(np.uint8)).resize((S.SIZE, S.SIZE), Image.BICUBIC), float)[..., None] / 255
    road = np.abs(arr - np.array(S.ASPHALT)).sum(-1) < 30
    bank &= ~wat & ~road
    arr[bank] = np.array(S.WOOD, float) * (0.85 + 0.3 * n1[bank])
    arr[wat] = np.array(S.WATER, float) * (0.9 + 0.2 * n1[wat])
    arr[foot] = (118, 116, 110)
    def block(x, z):
        i, j = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
        return bool(foot[i, j] or wat[i, j] or math.hypot(x, z) < 140.0)
    rng = np.random.default_rng(13)
    t = [(x, z, h, rad, rng.uniform(0.0, 1.0)) for x, z, h, rad in chm_trees(sys.argv[2], block)]
    # OpenStreetMap's own trees where the canopy map has none within 4 m (planted since its 2018-20 imagery).
    cell = {}
    for q in t:
        cell.setdefault((int(q[0] // 4), int(q[1] // 4)), []).append(q)
    for e in trees:
        x, z = S.model_xz(*e)
        if block(x, z) or any(math.hypot(q[0] - x, q[1] - z) < 4.0 for i in (-1, 0, 1) for j in (-1, 0, 1)
                              for q in cell.get((int(x // 4) + i, int(z // 4) + j), [])):
            continue
        h = rng.uniform(6.0, 12.0)
        t.append((x, z, h, h * 0.4, rng.uniform(0.0, 1.0)))
    t = np.array(t, "<f4").reshape(-1, 5)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
