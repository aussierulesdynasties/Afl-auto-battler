"""Norwood Oval's surroundings (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Kent Town and Norwood round the ground: The Parade, Woods Street, Beulah Road, Osmond Terrace and their
villas, cottages and townhouses, the Memorial Gardens, the schools and churches, painted 2 km a side at
1 m a pixel from OpenStreetMap, with every building stood up and the trees listed. It reuses the MCG's
painter (tools/grounds/mcg/surrounds.py) as Bellerive's does (tools/grounds/bellerive/surrounds.py). The
buildings that face the ground are modelled one by one in the model itself (model/town.py) and are left
out here.

    NORWOOD_IMG=<cache dir> python3 tools/grounds/norwood/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in nine tiles. Writes
assets/grounds/norwood/surrounds.webp, trees.bin and buildings.bin (the MCG's formats), in model
metres: x east, z south, the model's origin (the centre circle) at 0, 0.
Map data (c) OpenStreetMap contributors, ODbL. Building footprints: Microsoft Global ML Building
Footprints, ODbL. Canopy heights: Meta and WRI, CC BY 4.0.
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

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "norwood")
GLB = os.path.join(OUT, "norwood.glb")
# The model's origin: the centre circle (Google Earth's top-down mosaic; README.md).
S.LAT0, S.LON0 = -34.919825, 138.630446
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Each source moved onto Google Earth's frame (the model's): OpenStreetMap sits 0.5 m east and 2.0 m south of it
# (the pitch outline against the top-down mosaic, model/arena.py), Esri's imagery 2.3 m east and 0.5 m north
# (phase correlation of the grass edge and the fence). Metres east, north added to each source's positions.
OSM_SHIFT = (-0.5, 2.0)
ESRI_SHIFT = (-2.3, -0.5)
# Google Earth's Norwood in early summer: watered lawns in the parks, dry straw verges, grey-brown streets
# under heavy street trees, pale grey and terracotta roofs.
S.BASE = (132, 126, 98)
S.LAWN = (104, 126, 70)
S.PITCH = (96, 124, 66)
S.URBAN = (126, 122, 108)
S.PARKING = (112, 110, 106)
S.ASPHALT = (82, 82, 84)
S.ROOF = (154, 150, 142)
S.WATER = (60, 92, 96)
TILES = 3   # 3 x 3 OpenStreetMap tiles over 2.2 km
SPAN = 2200.0
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


def garden_trees(im, trees, ways, foot):
    """Trees in Norwood's back yards: on residential land that is clear of every road, roof and path
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


# Trees near the ground: OpenStreetMap lists only some of Norwood's trees (Osmond Terrace's planes, the
# Memorial Gardens' elms and the yards' gums are mostly missing), so within IMG_R every tree is stood where
# Meta and WRI's canopy height map has canopy 2 m or more, a tree every 6 m or so, as tall as the canopy it
# stands in and as wide as its patch. The map is open data (CC BY 4.0, cached in IMG_DIR).
IMG_R = 700.0
IMG_DIR = os.environ.get("NORWOOD_IMG", "/tmp/norwood_img")


# Tree heights: Meta and WRI's global canopy height map (1 m, from aerial and satellite imagery with
# GEDI lidar; AWS open data, CC BY 4.0), read as a window round the ground and cached in IMG_DIR. A tree
# takes the tallest canopy within its crown. Tall and narrow means a pine or cypress (the beach park's and
# the yards' conifers); the rest are planes, elms, gums and garden trees.
CHM_URL = ("/vsicurl/https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/"
           "311220303.tif")


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
    trees and of `blocked(x, z)` (the stadium and its own buildings). Shade 2 and up marks a pine or cypress."""
    from scipy import ndimage
    chm, to_px = canopy_height()
    r = IMG_R + 20.0
    e = np.arange(-r, r) + 0.5
    X, Z = np.meshgrid(e, e)                      # model metres, rows north to south (z is south)
    py, px = to_px(X, Z)
    H = chm[np.clip(py.astype(int), 0, chm.shape[0] - 1), np.clip(px.astype(int), 0, chm.shape[1] - 1)]
    # The canopy map misses big crowns round the ground (the elms and gums east of it read 0 m there), so
    # canopy is also measured from above: green, darker than lawn and rough. Where the map has no height a
    # crown's height comes from its width.
    img, _, _ = ortho_z(r, ROOF_Z, 1.0)
    a = img.astype(float)
    R_, G_, B_ = a[..., 0], a[..., 1], a[..., 2]
    L = (R_ + G_ + B_) / 3
    m = ndimage.uniform_filter(L, 5)
    tex = np.sqrt(np.maximum(ndimage.uniform_filter(L * L, 5) - m * m, 0))
    seen = (2 * G_ - R_ - B_ > 10) & (L < 110) & (tex > 7) & (G_ > R_ + 2)
    seen = ndimage.binary_closing(ndimage.binary_opening(seen), iterations=2)
    can = ndimage.binary_opening((H >= 2.0) | seen)
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
        h = top[ys[k], xs[k]]
        if h < 4.0:                                   # measured from above only: as tall as it is wide
            h = rad * 2.0 + rng.uniform(1.0, 3.0)
        h = float(np.clip(h, max(4.5, rad * 1.4), 32.0))
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
                p = os.path.join(IMG_DIR, "osm_%d%d.osm") % (i, j)
                if not os.path.exists(p):
                    fetch(i, j, p)
                paths.append(p)
    trees, ways = [], []
    seen = set()
    for p in paths:
        t, w = S.load(p)
        dx, dn = OSM_SHIFT                              # the loader's points are (east, north)
        t = [(e[0] + dx, e[1] + dn) for e in t]
        w = [(tg, [(q[0] + dx, q[1] + dn) for q in pts]) for tg, pts in w]
        for e in t:
            if e not in seen:
                seen.add(e)
                trees.append(e)
        for e in w:   # a way crossing a tile's edge comes back with both tiles: keep it once
            k = (tuple(sorted(e[0].items())), tuple(map(tuple, e[1])))
            if k not in seen:
                seen.add(k)
                ways.append(e)
    import trimesh
    from scipy import ndimage
    # The venue: its own edge (model/arena.py, the back of the walk) and the stands over it.
    sys.path.insert(0, os.path.join(HERE, "model"))
    import arena
    rad = arena.edge_radius(720)
    ven = Image.new("L", (S.SIZE, S.SIZE), 0)
    ImageDraw.Draw(ven).polygon([(r * math.cos(2 * math.pi * k / 720) + S.SIZE / 2, r * math.sin(2 * math.pi * k / 720) + S.SIZE / 2)
                                 for k, r in enumerate(rad)], fill=255)
    venue = np.asarray(ven) > 0
    # The buildings modelled one by one (model/town.py) and the ground's own corner buildings.
    own = plan_of(trimesh.load(GLB), ("town_", "north_", "wbcc", "ses_", "ws_"))
    foot = venue | ndimage.binary_dilation(own, iterations=1)

    def in_foot(pts):
        return any(foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                   for x, z in (S.model_xz(*q) for q in pts))

    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch"))
                                            and len(p) > 2 and in_foot(p))]
    for t, p in ways:
        if t.get("leisure") == "nature_reserve" or t.get("natural") == "wood":
            t.setdefault("leisure", "park")
    # Only the map's own square (the MCG painter reads every listed tree's pixel).
    trees = [e for e in trees if not in_foot([e]) and max(abs(c) for c in S.model_xz(*e)) < S.SIZE / 2 - 1]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).astype(float)
    gardens = [(x, z) for x, z in garden_trees(Image.fromarray(arr.astype(np.uint8)), trees, ways, foot)
               if math.hypot(x, z) > IMG_R]
    trees += [(x + S.PITCH_E, -z + S.PITCH_N) for x, z in gardens]
    arr = land_cover(arr, open_ground(trees, ways) & ~foot)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = S.tree_list(trees)
    if len(t):
        keep = [not foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                for x, z in t[:, :2]]
        t = t[keep]

    def blocked(x, z):
        i, j = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
        return bool(foot[i, j])
    img = canopy_trees([tuple(q) for q in t[:, :2]], blocked)
    t = np.concatenate([t.reshape(-1, 5), img]).astype("<f4")
    print("canopy trees", len(img))
    t, gums = sort_trees(t)
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    gums.astype("<f4").tofile(os.path.join(OUT, "gums.bin"))
    b = building_list(ways, in_foot)
    b = np.concatenate([b, ms_buildings(ways, in_foot)]).astype("<f4")
    b.tofile(os.path.join(OUT, "buildings.bin"))
    rc = roof_colours(b)
    rc.tofile(os.path.join(OUT, "roofs.bin"))
    print("roof colours", len(rc) // 3)
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


# The ground between the buildings. OpenStreetMap maps the streets and the houses but not what lies between them,
# which the map painted one dry tan: in Google Earth it is grey paving and drives, lawn, the shade of the yards'
# trees and some dry straw. Each metre of open ground (not a street, path, park, roof or water the map already
# paints) takes one of five classes read from the aerial imagery (Esri World Imagery, zoom 18) and is painted in
# that class's own flat colour, the median the imagery gives the class round the ground, mottled like the rest of
# the map. Only the class is kept, never the imagery's pixels (docs/MCG_STANDARD.md: sampled colours are fine).
# Measured 110-400 m from the centre (2026-11-26): grey 29%, straw 12%, lawn 20%, tree shade 25%, dark 12%.
COVER = {0: (150, 147, 139), 1: (138, 124, 100), 2: (112, 122, 84), 3: (74, 84, 56), 4: (150, 147, 139)}
SENTINEL = (255, 0, 255)


def open_ground(trees, ways):
    """The map's own open ground: the pixels it paints in its base or residential colour (painted again with
    those two in a colour nothing else uses)."""
    keep = S.BASE, S.URBAN
    S.BASE, S.URBAN = SENTINEL, SENTINEL
    try:
        im, _ = S.paint(list(trees), ways)
    finally:
        S.BASE, S.URBAN = keep
    a = np.asarray(im).astype(int)
    return (a[..., 0] > 150) & (a[..., 1] < 100) & (a[..., 2] > 150)


def cover_classes():
    """The imagery's class for every metre of the map (rows north to south, the origin in the middle):
    0 grey (paving, drives, unmapped roofs), 1 straw, 2 lawn, 3 tree shade, 4 dark (asphalt or shadow)."""
    from scipy import ndimage
    img, _, _ = ortho_z(S.SIZE / 2, ROOF_Z, 1.0)
    c = np.clip((img.astype(float) - 14.0) * 1.08, 0, 255)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    L, exg = c.mean(-1), 2 * g - r - b
    cls = np.zeros(L.shape, np.uint8)
    cls[(r - b > 28) & (exg <= 14)] = 1
    cls[exg > 14] = 2
    cls[(exg > 14) & (L < 75)] = 3
    cls[(cls == 0) & (L < 70)] = 4
    cls = ndimage.median_filter(cls, size=3)
    # A building's shadow is not the ground's colour: a dark patch smaller than a car park takes the class
    # most common round it.
    dark = cls == 4
    lab, n = ndimage.label(dark)
    big = np.isin(lab, 1 + np.nonzero(ndimage.sum(dark, lab, range(1, n + 1)) >= 150)[0])
    small = dark & ~big
    votes = np.stack([ndimage.uniform_filter((cls == k).astype(float), 9) for k in range(4)])
    cls[small] = np.argmax(votes, 0)[small]
    return cls


def land_cover(arr, ground):
    """`arr` (the painted map) with its open ground painted by class."""
    cls = cover_classes()
    rng = np.random.default_rng(11)
    n1 = np.asarray(Image.fromarray((rng.random((128, 128)) * 255).astype(np.uint8)).resize((S.SIZE, S.SIZE), Image.BICUBIC), float) / 255
    mott = 1.0 + (n1 - 0.5) * 0.16 + (rng.random((S.SIZE, S.SIZE)) - 0.5) * 0.06
    pal = np.array([COVER[k] for k in range(5)], float)
    paint = pal[cls] * mott[..., None]
    out = arr.copy()
    out[ground] = paint[ground]
    for k in range(5):
        print("open ground class %d: %.0f%%" % (k, 100.0 * (cls[ground] == k).mean()))
    return out


# Trees seen from above. Within IMG_R the list stood 44% of the land under a crown where the imagery shows about
# 28% (dark canopy 25%, Meta's canopy map 20% at 2 m and up; 110-400 m, 2026-11-26): a crown is kept only where
# the imagery shows leaves under most of it, and no wider than its leaves reach. A crown the imagery shows grey-green
# and broad is a eucalypt, drawn as one (GroundModels SURROUNDS "gum_trees"); the bright green ones are the planes,
# elms and garden trees.
def sort_trees(t):
    from scipy import ndimage
    cls = cover_classes()
    img, _, _ = ortho_z(S.SIZE / 2, ROOF_Z, 1.0)
    c = img.astype(float)
    exg = 2 * c[..., 1] - c[..., 0] - c[..., 2]
    leaf = (cls == 2) | (cls == 3)
    reach = ndimage.distance_transform_edt(leaf)
    keep, gum = [], []
    for row in t:
        x, z, h, rad, shade = row
        i, j = int(z + S.SIZE / 2), int(x + S.SIZE / 2)
        if not (0 <= i < S.SIZE and 0 <= j < S.SIZE) or math.hypot(x, z) > IMG_R:
            keep.append(True); gum.append(False)
            continue
        rr = max(1, int(rad))
        win = (slice(max(0, i - rr), i + rr + 1), slice(max(0, j - rr), j + rr + 1))
        yy, xx = np.mgrid[win[0], win[1]]
        disc = (yy - i) ** 2 + (xx - j) ** 2 <= rad * rad
        on = leaf[win][disc]
        ok = on.mean() >= 0.55 if on.size else False
        keep.append(ok)
        if ok:
            row[3] = float(np.clip(min(rad, reach[i, j] * 1.15 + 1.0), 2.2, rad))
            g = exg[win][disc & leaf[win]]
            gum.append(shade < 2.0 and h >= 8.0 and row[3] >= 3.5 and g.size > 0 and np.median(g) < 22)
        else:
            gum.append(False)
    keep, gum = np.array(keep), np.array(gum)
    print("trees kept %d of %d, %d of them eucalypts" % (keep.sum(), len(t), (keep & gum).sum()))
    return t[keep & ~gum], t[keep & gum]


def building_list(ways, in_foot):
    """GMHBA's rule: untagged blocks under 400 m2 and the mapped houses are single-storey houses under a
    hipped roof (a negative height): Norwood's villas and cottages are mostly single-storey under hipped iron."""
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


# OpenStreetMap has drawn most of Norwood's houses but not all. The rest come from Microsoft's Global ML
# Building Footprints (ODbL, like OpenStreetMap; footprints traced by machine from aerial photos, each with
# an estimated height), the tile round Adelaide, cached in IMG_DIR. A footprint is kept only where no
# OpenStreetMap building already stands.
MSB_URL = ("https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/global-buildings.geojsonl/"
           "RegionName=Australia/quadkey=311220303/part-00150-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz")


def ms_buildings(ways, in_foot):
    import gzip
    import json
    path = os.path.join(IMG_DIR, "msb_311220303.csv.gz")
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
            if taken[cz, cx]:
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


# Roof colours: each building's roof takes the median colour seen inside its footprint from above (Esri World
# Imagery, zoom 18, about 0.5 m a pixel, cached in IMG_DIR). Only the sampled colour is kept, one per
# building (docs/MCG_STANDARD.md: sampled colours are fine, raw imagery never ships).
ROOF_Z = 18
ROOF_R = 960.0


def ortho_z(r=ROOF_R, z=ROOF_Z, step=0.5):
    """Imagery resampled to model metres at `step` m a pixel, north up, the origin in the middle."""
    d = os.path.join(IMG_DIR, "esri%d" % z)
    os.makedirs(d, exist_ok=True)
    n = 2 ** z

    def txy(lat, lon):
        return ((lon + 180) / 360 * n,
                (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n)
    dlat, dlon = r / 110574.0, r / (111320.0 * math.cos(math.radians(S.LAT0)))
    x0, y0 = txy(S.LAT0 + dlat, S.LON0 - dlon)
    x1, y1 = txy(S.LAT0 - dlat, S.LON0 + dlon)
    X0, Y0 = int(x0), int(y0)
    M = np.zeros(((int(y1) - Y0 + 1) * 256, (int(x1) - X0 + 1) * 256, 3), np.uint8)
    for i in range(X0, int(x1) + 1):
        for j in range(Y0, int(y1) + 1):
            p = os.path.join(d, "%d_%d.jpg" % (i, j))
            if not os.path.exists(p):
                req = urllib.request.Request("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
                                             "MapServer/tile/%d/%d/%d" % (z, j, i), headers={"User-Agent": "afl-ground-builder/1.0"})
                with urllib.request.urlopen(req, timeout=60) as rr, open(p, "wb") as f:
                    f.write(rr.read())
            M[(j - Y0) * 256:(j - Y0 + 1) * 256, (i - X0) * 256:(i - X0 + 1) * 256] = \
                np.asarray(Image.open(p).convert("RGB"))
    e = np.arange(-r, r, step) + step / 2
    E, N = np.meshgrid(e, -e)
    E, N = E - ESRI_SHIFT[0], N - ESRI_SHIFT[1]      # model metres -> where the imagery shows them
    x, y = txy(S.LAT0 + N / 110574.0, S.LON0 + E / (111320.0 * math.cos(math.radians(S.LAT0))))
    px = np.clip(((x - X0) * 256).astype(int), 0, M.shape[1] - 1)
    py = np.clip(((y - Y0) * 256).astype(int), 0, M.shape[0] - 1)
    return M[py, px], r, step


def roof_colours(buf):
    """One linear-light RGB triple per building in a buildings.bin buffer: the median of its roof from above,
    taken 0.7 m inside its walls (no eave shadow, no gutter), lifted out of the imagery's haze."""
    img, r, step = ortho_z()
    W = img.shape[0]
    out = []
    i = 0
    while i + 1 < len(buf):
        n = int(buf[i])
        pts = buf[i + 2:i + 2 + 2 * n].reshape(-1, 2)
        i += 2 + 2 * n
        m = Image.new("L", (W, W), 0)
        q = [((x + r) / step, (z + r) / step) for x, z in pts]        # z is south: rows run north to south
        ImageDraw.Draw(m).polygon(q, fill=255)
        bx0, by0 = max(0, int(min(a for a, _ in q)) - 2), max(0, int(min(b for _, b in q)) - 2)
        bx1, by1 = min(W, int(max(a for a, _ in q)) + 3), min(W, int(max(b for _, b in q)) + 3)
        mm = np.asarray(m.crop((bx0, by0, bx1, by1)).filter(ImageFilter.MinFilter(3))) > 0
        if mm.sum() < 4:
            mm = np.asarray(m.crop((bx0, by0, bx1, by1))) > 0
        px = img[by0:by1, bx0:bx1][mm] if mm.any() else np.array([[150, 150, 146]])
        # A footprint's overhanging trees and the shadow of its neighbour are not its roof (a quarter of the roofs
        # came out olive or brown, 2026-11-26): only the roof's own grey, white or red is sampled.
        f = px.astype(float)
        roof = (2 * f[:, 1] - f[:, 0] - f[:, 2] <= 10) & (f.mean(-1) >= 70)
        if roof.sum() >= max(4, 0.15 * len(f)):
            px = px[roof]
        else:
            px = np.array([[150, 150, 146]])
        c = np.median(px.astype(float), axis=0)
        # The aerial's haze lifts the darks and greys the colours: take 14 off and stretch back.
        c = np.clip((c - 14.0) * 1.08, 8, 255) / 255.0
        out += list(c ** 2.2)
    return np.array(out, "<f4")


if __name__ == "__main__":
    main()
