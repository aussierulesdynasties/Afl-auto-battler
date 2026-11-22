"""Bellerive Oval's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Bellerive's streets and houses, Bellerive Beach and Beach Park, Kangaroo Bay and the Derwent, the PCYC
and the ovals and courts east of the ground, painted 2 km a side at 1 m a pixel, with every building
stood up and the trees listed. It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with
Bellerive's place and colours, as GMHBA's does (tools/grounds/gmhba/surrounds.py), and adds the sea:
OpenStreetMap draws the shore as open coastline lines, so the water is filled from the open estuary
up to them.

    python3 tools/grounds/bellerive/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in nine tiles. Writes
assets/grounds/bellerive/surrounds.webp, trees.bin and buildings.bin (the MCG's formats), in model
metres: x east, z south, the model's origin (the OSM pitch's centre) at 0, 0.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("mcg_surrounds", os.path.join(HERE, "..", "mcg", "surrounds.py"))
S = importlib.util.module_from_spec(_spec)   # the MCG's painter (this file shares its name)
_spec.loader.exec_module(S)

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "bellerive")
GLB = os.path.join(OUT, "bellerive.glb")
# The model's origin: the centre of the OSM pitch outline's bounding box (work/geo.py).
S.LAT0, S.LON0 = -42.8773092, 147.3737365
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Google Earth's Bellerive in summer: dry yellow-olive grass, grey-brown house blocks with green gardens.
S.BASE = (128, 128, 86)
S.LAWN = (112, 126, 74)
S.PITCH = (100, 118, 70)   # Google Earth: the training ovals are duller than the main ground
S.URBAN = (120, 123, 100)
S.PARKING = (110, 108, 104)
S.ASPHALT = (84, 84, 86)
S.ROOF = (150, 146, 138)
S.WATER = (46, 92, 108)
SAND = (214, 198, 160)
SHALLOW = (74, 130, 136)
# Open water: a point well out in the Derwent (south of Bellerive Beach), m east/north of the origin.
SEA_SEEDS = [(0.0, -900.0), (-950.0, -300.0), (-600.0, 640.0)]
TILES = 3   # 3 x 3 OpenStreetMap tiles over 2.2 km
SPAN = 2200.0
# Gardens: Bellerive's yards carry a tree every 28 m or so in Google Earth, smaller than the parks'.
GARDEN_DENSITY = 1.0 / 420.0


def fetch(i, j, path):
    dlat = SPAN / 110574.0 / TILES
    dlon = SPAN / (111320.0 * math.cos(math.radians(S.LAT0))) / TILES
    lat0 = S.LAT0 - SPAN / 2 / 110574.0
    lon0 = S.LON0 - SPAN / 2 / (111320.0 * math.cos(math.radians(S.LAT0)))
    a, b = lon0 + i * dlon, lat0 + j * dlat
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (a, b, a + dlon, b + dlat)
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def footprint():
    """The stadium's plan as a 1 m mask in the map's pixels (GMHBA's method): the model draws it."""
    import trimesh
    sc = trimesh.load(GLB)
    v = sc.to_geometry().vertices if hasattr(sc, "to_geometry") else sc.dump(concatenate=True).vertices
    v = v[v[:, 1] > 0.5]
    # The light towers' lamp heads stand well off the bowl; only the bowl closes the footprint.
    v = v[np.hypot(v[:, 0], v[:, 2]) < 112.0]
    m = np.zeros((S.SIZE, S.SIZE), bool)
    ix = np.clip((v[:, 0] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    iz = np.clip((v[:, 2] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    m[iz, ix] = True
    a = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
    yy, xx = np.mgrid[0:S.SIZE, 0:S.SIZE]
    ang = np.arctan2(yy - S.SIZE / 2, xx - S.SIZE / 2)
    rr = np.hypot(yy - S.SIZE / 2, xx - S.SIZE / 2)
    bins = ((ang + math.pi) / (2 * math.pi) * 720).astype(int) % 720
    rmax = np.zeros(720)
    np.maximum.at(rmax, bins[a], rr[a])
    rmax = np.maximum(rmax, np.roll(rmax, 1))
    rmax = np.maximum(rmax, np.roll(rmax, -1))
    out = a | (rr <= rmax[bins])
    # The indoor centre west of the Ponting and its forecourt stand outside that circle; their own plans
    # join the footprint.
    return out | plan_of(sc, ("indoor_centre", "forecourt"))


def plan_of(sc, names):
    """The plan of the model's meshes whose names start with one of `names`, as a 1 m mask, holes filled."""
    from scipy import ndimage
    out = np.zeros((S.SIZE, S.SIZE), bool)
    for name, g in sc.geometry.items():
        if name.startswith(names):
            w = np.asarray(g.vertices)
            b = np.zeros((S.SIZE, S.SIZE), bool)
            b[np.clip((w[:, 2] + S.SIZE / 2).astype(int), 0, S.SIZE - 1),
              np.clip((w[:, 0] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)] = True
            out |= ndimage.binary_fill_holes(ndimage.binary_dilation(b, iterations=2))
    return out


def sea_mask(ways):
    """Water: everything reachable from SEA_SEEDS without crossing the coastline. Each open end of a
    coastline line is carried 700 m on along its last bearing, so the fill cannot run round it."""
    from scipy import ndimage
    wall = Image.new("L", (S.SIZE, S.SIZE), 0)
    d = ImageDraw.Draw(wall)
    for t, p in ways:
        if t.get("natural") != "coastline" or len(p) < 2:
            continue
        pts = [S.px(*q) for q in p]
        if p[0] != p[-1]:
            for a, b in ((pts[1], pts[0]), (pts[-2], pts[-1])):
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy) or 1.0
                ext = (b[0] + dx / L * 700, b[1] + dy / L * 700)
                d.line([b, ext], fill=255, width=3)
        d.line(pts, fill=255, width=3)
    free = np.asarray(wall) == 0
    lab, _ = ndimage.label(free)
    sea = np.zeros_like(free)
    for e, n in SEA_SEEDS:
        x, y = S.px(e, n)
        k = lab[int(y), int(x)]
        if k:
            sea |= lab == k
    # The drawn coastline itself is the water's edge: give its pixels to the sea.
    sea |= ndimage.binary_dilation(sea, iterations=2) & ~free
    return sea


def garden_trees(im, trees, ways, foot):
    """Trees in Bellerive's back yards: on residential land that is clear of every road, roof and path
    by 3 m, at GARDEN_DENSITY, never nearer than 8 m to another."""
    a = np.asarray(im, int)
    res = Image.new("L", (S.SIZE, S.SIZE), 0)
    rd = ImageDraw.Draw(res)
    for t, p in ways:
        if t.get("landuse") == "residential" and len(p) > 3:
            rd.polygon([S.px(*q) for q in p], fill=255)
    ok = (np.asarray(res) > 0) & (np.abs(a - np.array(S.URBAN)).sum(-1) < 40) & ~foot
    ok = np.asarray(Image.fromarray((~ok * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) == 0
    ys, xs = np.nonzero(ok)
    rng = np.random.default_rng(31)
    want = int(len(xs) * GARDEN_DENSITY)
    cell, out = {}, []
    for e, n in trees:
        x, z = S.model_xz(e, n)
        cell.setdefault((int(x // 8), int(z // 8)), []).append((x, z))
    for _ in range(want * 6):
        if len(out) >= want:
            break
        k = rng.integers(len(xs))
        x, z = xs[k] - S.SIZE / 2 + rng.random(), ys[k] - S.SIZE / 2 + rng.random()
        cx, cz = int(x // 8), int(z // 8)
        near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cz + j), [])]
        if any((qx - x) ** 2 + (qz - z) ** 2 < 64 for qx, qz in near):
            continue
        cell.setdefault((cx, cz), []).append((x, z))
        out.append((x, z))
    return out


# Trees near the ground: OpenStreetMap lists few of Bellerive's trees (the beach park's pines and gums, the
# yards' trees), so within IMG_R every tree is stood where Meta and WRI's canopy height map has canopy
# 2 m or more, a tree every 6 m or so, as tall as the canopy it stands in and as wide as its patch.
# The map is open data (CC BY 4.0, cached in IMG_DIR); no aerial photo is used (the ones that show
# Bellerive best, Esri's and the LIST's, do not allow derived data).
IMG_R = 700.0
IMG_DIR = os.environ.get("BELLERIVE_IMG", "/tmp/bellerive_img")


# Tree heights: Meta and WRI's global canopy height map (1 m, from aerial and satellite imagery with
# GEDI lidar; AWS open data, CC BY 4.0), read as a window round the ground and cached in IMG_DIR. A tree
# takes the tallest canopy within its crown. Tall and narrow means a pine or cypress (the beach park's and
# the yards' conifers in Google Earth); the rest are gums and garden trees.
CHM_URL = ("/vsicurl/https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/"
           "313010023.tif")


def canopy_height(r=IMG_R + 60.0):
    """(heights, to_px): the canopy height map in metres and a function from model (x, z) to its pixel."""
    cache = os.path.join(IMG_DIR, "chm.npz")
    class tf:                                      # lon, lat -> web mercator metres (EPSG:3857)
        @staticmethod
        def transform(lon, lat):
            return (np.radians(lon) * 6378137.0,
                    np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)) * 6378137.0)
    dlat, dlon = r / 110574.0, r / (111320.0 * math.cos(math.radians(S.LAT0)))
    if not os.path.exists(cache):
        import rasterio
        from rasterio.windows import from_bounds
        with rasterio.open(CHM_URL) as src:
            x0, y0 = tf.transform(S.LON0 - dlon, S.LAT0 - dlat)
            x1, y1 = tf.transform(S.LON0 + dlon, S.LAT0 + dlat)
            w = from_bounds(x0, y0, x1, y1, src.transform)
            a = src.read(1, window=w).astype(np.float32)
            t = src.window_transform(w)
            np.savez(cache, a=a, t=np.array([t.c, t.a, t.f, t.e]))
    z = np.load(cache)
    a, (c, sx, f, sy) = z["a"], z["t"]

    def to_px(x, zz):
        lon = S.LON0 + x / (111320.0 * math.cos(math.radians(S.LAT0)))
        lat = S.LAT0 - zz / 110574.0
        mx, my = tf.transform(lon, lat)
        return (my - f) / sy, (mx - c) / sx
    return a, to_px


def canopy_trees(existing, blocked):
    """(x, z, height, crown radius, shade) rows for the canopy within IMG_R, clear of `existing` (x, z)
    trees and of `blocked(x, z)` (the stadium, the sea). Shade 2 and up marks a pine or cypress."""
    from scipy import ndimage
    chm, to_px = canopy_height()
    r = IMG_R + 20.0
    e = np.arange(-r, r) + 0.5
    X, Z = np.meshgrid(e, e)                      # model metres, rows north to south (z is south)
    py, px = to_px(X, Z)
    H = chm[np.clip(py.astype(int), 0, chm.shape[0] - 1), np.clip(px.astype(int), 0, chm.shape[1] - 1)]
    can = ndimage.binary_opening(H >= 2.0)
    lab, n = ndimage.label(can)
    can &= np.isin(lab, 1 + np.nonzero(ndimage.sum(can, lab, range(1, n + 1)) >= 8)[0])
    dist = ndimage.distance_transform_edt(can)
    top = ndimage.maximum_filter(H, size=7)
    ys, xs = np.nonzero(can)
    order = np.argsort(-dist[ys, xs], kind="stable")
    rng = np.random.default_rng(23)
    cell = {}
    for x, z in existing:
        cell.setdefault((int(x // 10), int(z // 10)), []).append((x, z, 2.5))
    out = []
    for k in order:
        x, z = xs[k] - r + 0.5, ys[k] - r + 0.5
        if math.hypot(x, z) > IMG_R or blocked(x, z):
            continue
        rad = float(np.clip(dist[ys[k], xs[k]] * 1.3, 2.6, 7.0))
        cx, cz = int(x // 10), int(z // 10)
        near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cz + j), [])]
        if any(math.hypot(qx - x, qz - z) < max(5.5, 0.85 * (rad + qr)) for qx, qz, qr in near):
            continue
        cell.setdefault((cx, cz), []).append((x, z, rad))
        # The map's heights run low on small crowns (its 1 m cells average them): never shorter than the
        # crown is wide.
        h = float(np.clip(top[ys[k], xs[k]], max(4.5, rad * 1.4), 32.0))
        shade = rng.uniform(0.0, 1.0)
        if h >= 11.0 and h > 3.0 * rad:            # tall and narrow: a pine or cypress
            rad = float(np.clip(h * 0.2, 2.2, rad)); shade += 2.0
        out.append((x, z, h, rad, shade))
    return np.array(out, "<f4").reshape(-1, 5)


def main():
    paths = sys.argv[1:]
    if not paths:
        for i in range(TILES):
            for j in range(TILES):
                p = "/tmp/bellerive_osm_%d%d.osm" % (i, j)
                if not os.path.exists(p):
                    fetch(i, j, p)
                paths.append(p)
    trees, ways = [], []
    seen = set()
    for p in paths:
        t, w = S.load(p)
        for e in t:
            if e not in seen:
                seen.add(e)
                trees.append(e)
        for e in w:   # a way crossing a tile's edge comes back with both tiles: keep it once
            k = (tuple(sorted(e[0].items())), tuple(map(tuple, e[1])))
            if k not in seen:
                seen.add(k)
                ways.append(e)
    foot = footprint()
    import trimesh
    nets = plan_of(trimesh.load(GLB), ("practice_nets",))   # no trees in the nets; the lawn stays

    def in_foot(pts):
        return any(foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                   for x, z in (S.model_xz(*q) for q in pts))

    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch"))
                                            and len(p) > 2 and in_foot(p))]
    # Nature reserves and the beach park's woods are filled with trees like a park.
    for t, p in ways:
        if t.get("leisure") == "nature_reserve" or t.get("natural") == "wood":
            t.setdefault("leisure", "park")
    trees = [e for e in trees if not in_foot([e])]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).astype(float)
    sea = sea_mask(ways)
    # Beach: OpenStreetMap's sand, then the water over it, a lighter band in the shallows.
    sand = Image.new("L", (S.SIZE, S.SIZE), 0)
    sd = ImageDraw.Draw(sand)
    for t, p in ways:
        if t.get("natural") == "beach" and len(p) > 2:
            sd.polygon([S.px(*q) for q in p], fill=255)
    sand = np.asarray(sand) > 0
    arr[sand] = SAND
    from scipy import ndimage
    dist = ndimage.distance_transform_edt(sea)
    shallow = np.clip(1.0 - dist / 60.0, 0, 1)[..., None]
    water = np.array(S.WATER, float) * (1 - shallow) + np.array(SHALLOW, float) * shallow
    rng = np.random.default_rng(5)
    ripple = np.asarray(Image.fromarray((rng.random((512, 512)) * 255).astype(np.uint8))
                        .resize((S.SIZE, S.SIZE), Image.BICUBIC), float)[..., None] / 255 - 0.5
    water = water * (1 + ripple * 0.08)
    arr = np.where(sea[..., None], water, arr)
    arr[foot] = (118, 116, 110)
    trees = [e for e in trees if not sea[tuple(int(c) for c in S.px(*e)[::-1])]]
    gardens = [(x, z) for x, z in garden_trees(Image.fromarray(arr.astype(np.uint8)), trees, ways, foot | sea)
               if math.hypot(x, z) > IMG_R]
    trees += [(x + S.PITCH_E, -z + S.PITCH_N) for x, z in gardens]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = S.tree_list(trees)
    if len(t):
        keep = [not (foot | nets)[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                for x, z in t[:, :2]]
        t = t[keep]
    def blocked(x, z):
        i, j = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
        return bool(foot[i, j] or nets[i, j] or sea[i, j] or math.hypot(x, z) < 105.0)
    img = canopy_trees([tuple(q) for q in t[:, :2]], blocked)
    t = np.concatenate([t.reshape(-1, 5), img]).astype("<f4")
    print("canopy trees", len(img))
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b = np.concatenate([b, ms_buildings(ways, in_foot, sea)]).astype("<f4")
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b), "sea px", int(sea.sum()))


def building_list(ways, in_foot):
    """GMHBA's rule: untagged blocks under 400 m2 and the mapped houses are single-storey houses under a
    hipped roof (a negative height); Bellerive is the same weatherboard and brick suburb."""
    out = []
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        pts = [S.model_xz(*q) for q in p[:-1]]
        if in_foot(p) or max(max(abs(x), abs(z)) for x, z in pts) > 950:
            continue
        h = S.building_height(t)
        if h < 2.5:
            continue
        a = abs(S._area(np.array(pts + pts[:1])))
        if "height" not in t and t.get("building") in ("house", "detached", "semidetached_house", "bungalow", "yes") \
                and a < 400.0:
            lv = t.get("building:levels")
            h = -3.0 if lv in (None, "1") else -(float(lv) * 3.0)
        elif t.get("building") in ("garage", "shed", "carport"):
            h = 2.8
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    return np.array(out, "<f4")


# OpenStreetMap has drawn about a third of Bellerive's houses. The rest come from Microsoft's Global ML
# Building Footprints (ODbL, like OpenStreetMap; footprints traced by machine from aerial photos, each with
# an estimated height), the tile round Hobart, cached in IMG_DIR. A footprint is kept only where no
# OpenStreetMap building already stands.
MSB_URL = ("https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/global-buildings.geojsonl/"
           "RegionName=Australia/quadkey=313010023/part-00065-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz")


def ms_buildings(ways, in_foot, sea):
    import gzip
    import json
    path = os.path.join(IMG_DIR, "msb_313010023.csv.gz")
    if not os.path.exists(path):
        os.makedirs(IMG_DIR, exist_ok=True)
        urllib.request.urlretrieve(MSB_URL, path)
    taken = Image.new("L", (S.SIZE, S.SIZE), 0)
    td = ImageDraw.Draw(taken)
    for t, p in ways:
        if "building" in t and len(p) > 2:
            td.polygon([S.px(*q) for q in p], fill=255)
    taken = np.asarray(taken.filter(ImageFilter.MaxFilter(3))) > 0
    lat_r, lon_r = 1000.0 / 110574.0, 1000.0 / (111320.0 * math.cos(math.radians(S.LAT0)))
    out, n = [], 0
    with gzip.open(path, "rt") as f:
        for line in f:
            g = json.loads(line)
            ring = g["geometry"]["coordinates"][0]
            lon, lat = ring[0]
            if abs(lat - S.LAT0) > lat_r or abs(lon - S.LON0) > lon_r:
                continue
            en = [S.en(la, lo) for lo, la in ring[:-1]]
            pts = [S.model_xz(*q) for q in en]
            if len(pts) < 3 or max(max(abs(x), abs(z)) for x, z in pts) > 950 or in_foot(en):
                continue
            cx = int(np.clip(np.mean([x for x, _ in pts]) + S.SIZE / 2, 0, S.SIZE - 1))
            cz = int(np.clip(np.mean([z for _, z in pts]) + S.SIZE / 2, 0, S.SIZE - 1))
            if taken[cz, cx] or sea[cz, cx]:
                continue
            a = abs(S._area(np.array(pts + pts[:1])))
            if a < 12.0:                           # sheds and cars under the trace's noise
                continue
            hm = float(g["properties"].get("height") or -1.0)
            if a < 40.0:
                h = 2.8                            # garages and sheds
            elif a < 400.0:
                h = -3.0 if hm < 5.5 else -6.0     # a house: one storey, or two where the trace is tall
            else:
                h = float(np.clip(hm if hm > 2.5 else 7.0, 3.0, 30.0))
            out.append(float(len(pts)))
            out.append(h)
            for x, z in pts:
                out += [x, z]
            n += 1
    print("microsoft buildings", n)
    return np.array(out, "<f4")


if __name__ == "__main__":
    main()
