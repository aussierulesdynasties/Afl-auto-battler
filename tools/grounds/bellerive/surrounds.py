"""Bellerive Oval's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Bellerive's streets and houses, Bellerive Beach and Beach Park, Kangaroo Bay and the Derwent, the PCYC
and the ovals and courts east of the ground, painted 2 km a side at 1 m a pixel, with every building
stood up and the trees listed. It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with
Bellerive's place and colours, as GMHBA's does (tools/grounds/gmhba/surrounds.py), and adds the sea:
OpenStreetMap draws the shore as open coastline lines, so the water is filled from the open estuary
up to them.

    python3 tools/grounds/bellerive/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in nine tiles. Writes
assets/grounds/bellerive/surrounds.webp (and surrounds_near.webp, 768 m at 0.375 m), trees.bin and buildings.bin (the MCG's formats), in model
metres: x east, z south, the model's origin (the OSM pitch's centre) at 0, 0.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import json
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


# Tree heights: Meta and WRI's global canopy height map (1 m, from aerial and satellite imagery with GEDI
# lidar; AWS open data, CC BY 4.0), read as a window round the ground and cached in IMG_DIR. A traced tree
# takes the tallest canopy within its crown where the map has one.
IMG_R = 700.0
IMG_DIR = os.environ.get("BELLERIVE_IMG", "/tmp/bellerive_img")
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


# The fence's ellipse (GroundModels.FIT["bellerive"]: centre x, z, long axis deg, half length, half width)
# and the apron behind it. Trees stay out of it; past it the stadium's own plan (footprint) blocks them.
# A plain 105 m circle stood here before and cut the tall gums along the east side's grass bank, which
# Google Earth shows 85-105 m from the centre (measured 2026-11-23: canopy 13% there in Google Earth, 5% ours).
FIELD = (0.31, -0.64, 68.7, 86.9, 66.77)
APRON = 9.0


def in_field(x, z):
    cx, cz, ang, hl, hw = FIELD
    a = math.radians(ang)
    u = (x - cx) * math.cos(a) + (z - cz) * math.sin(a)
    v = -(x - cx) * math.sin(a) + (z - cz) * math.cos(a)
    return (u / (hl + APRON)) ** 2 + (v / (hw + APRON)) ** 2 < 1.0


def canopy_trees(blocked):
    """(x, z, height, crown radius, kind) rows filling Google Earth's canopy (ge_ground.py's canopy class, 1 m) with
    crowns, as dense as Google Earth shows it: a garden's clump or the gums along the beach are one mass of
    overlapping crowns, not a tree traced at each blob's middle (PC check r5: evenly spread lollipops). Crowns go
    in widest first, each as wide as the canopy's depth round it (1.2 to 7 m), none nearer another than 0.7 of their
    two radii; each takes the canopy height map's tallest within it (Meta and WRI, CC BY 4.0), and a crown the map
    reads under 3 m is a crown and a half's width tall (the map reads most of Bellerive's gums under it), or a
    shrub in a patch under 15 m2. Tall and narrow means a pine or cypress."""
    from scipy import ndimage
    raw = np.load(os.path.join(HERE, "ge_ground.npz"))["cls"]
    can = ndimage.binary_closing(raw == 5, np.ones((3, 3)))     # a crown's gaps and shade are still the crown
    can = ndimage.binary_opening(can, np.ones((2, 2)))           # single pixels are speckle, not a tree
    lab, nl = ndimage.label(can)
    area = np.bincount(lab.ravel())
    yy, xx = np.nonzero(can)
    x = xx - S.SIZE / 2 + 0.5
    z = yy - S.SIZE / 2 + 0.5
    ok = np.hypot(x, z) < 1000.0                                  # the map fades to plain town from 1,000 m
    ok &= np.array([not blocked(a, b) for a, b in zip(x, z)])
    depth = ndimage.distance_transform_edt(can)[yy, xx]
    blob = area[lab[yy, xx]]
    x, z, depth, blob = x[ok], z[ok], depth[ok], blob[ok]
    order = np.argsort(-depth, kind="stable")
    chm, to_px = canopy_height(r=S.SIZE / 2 + 40.0)
    rng = np.random.default_rng(23)
    cell = {}
    out = []
    for k in order:
        r = float(np.clip(depth[k] * 1.15 + 0.6, 1.8, 7.0))
        a, b = float(x[k]), float(z[k])
        ci, cj = int(a // 8), int(b // 8)
        clash = False
        for i in range(ci - 2, ci + 3):
            for j in range(cj - 2, cj + 3):
                for (qa, qb, qr) in cell.get((i, j), ()):
                    if (qa - a) ** 2 + (qb - b) ** 2 < (0.78 * (r + qr)) ** 2:
                        clash = True
                        break
                if clash:
                    break
            if clash:
                break
        if clash:
            continue
        cell.setdefault((ci, cj), []).append((a, b, r))
        py, px = to_px(a, b)
        h = 0.0
        n = max(3, int(math.ceil(r)))
        i0, j0 = int(py), int(px)
        if n <= i0 < chm.shape[0] - n and n <= j0 < chm.shape[1] - n:
            h = float(chm[i0 - n:i0 + n + 1, j0 - n:j0 + n + 1].max())
        if h < 3.0:
            if blob[k] < 15:
                h = float(np.clip(1.4 * r + 0.6, 1.8, 5.0))       # a lone patch that small: a shrub or a hedge
            else:                                                 # the height map misses most of Bellerive's
                h = max(4.5, r * 2.0 * rng.uniform(1.3, 1.8))     # gums: a crown and a half's width or so
        h = float(np.clip(h, r * 1.25, 30.0))
        shade = rng.uniform(0.0, 1.0)
        if h >= 14.0 and h > 4.0 * r:
            r = float(np.clip(h * 0.2, 2.2, r)); shade += 2.0
        out.append((a, b, h, r, shade))
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
    # Every other tree fills Google Earth's canopy (canopy_trees): no park or garden fill.
    S.PARK_DENSITY = 0.0
    n_osm = len(trees)
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

    def blocked(x, z):
        i, j = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
        return bool(foot[i, j] or nets[i, j] or sea[i, j] or sand[i, j] or in_field(x, z))
    trees = [e for e in trees[:n_osm] if not sea[tuple(int(c) for c in S.px(*e)[::-1])]]
    t = S.tree_list(trees).reshape(-1, 5)
    can = canopy_trees(blocked)
    # A tree OpenStreetMap maps stays where Google Earth shows no canopy round it; in the canopy the fill has it.
    from scipy import ndimage
    near_can = ndimage.binary_dilation(np.load(os.path.join(HERE, "ge_ground.npz"))["cls"] == 5, np.ones((7, 7)))
    if len(t):
        keep = [not (blocked(x, z) or near_can[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)),
                                              int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]) for x, z in t[:, :2]]
        t = t[keep]
    n_map = len(t)
    t = np.concatenate([t, can]).astype("<f4")
    arr = ge_ground(arr, ways, sea, foot, t)
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
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    near = near_map(arr, ways, sea, sand, foot, t)
    if near is not None:
        near.save(os.path.join(OUT, "surrounds_near.webp"), quality=88, method=6)
    print("OpenStreetMap trees", n_map, "canopy trees", len(can))
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b = np.concatenate([b, ms_buildings(ways, in_foot, sea)]).astype("<f4")
    b, rgb = from_google_earth(b)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    rgb.tofile(os.path.join(OUT, "roofs.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b), "sea px", int(sea.sum()))


def _ground_classes():
    """(coarse 1 m classes, fine 0.375 m classes, palette, fine span m) from ge_ground.py, each grid's unknown cells
    (canopy, roofs, shadow) taking the nearest known class round them; None where the file is missing."""
    from scipy import ndimage
    f = os.path.join(HERE, "ge_ground.npz")
    if not os.path.exists(f):
        return None
    z = np.load(f)
    info = json.load(open(os.path.join(HERE, "ge_ground.json")))
    pal = np.zeros((256, 3))
    for k, name in enumerate(info["names"]):
        if name in info["colour"]:
            pal[k] = info["colour"][name]
    measured = [k for k, n in enumerate(info["names"]) if n in info["colour"]]

    def filled(cls):
        _, (ii, jj) = ndimage.distance_transform_edt(~np.isin(cls, measured), return_indices=True)
        return cls[ii, jj]
    return filled(z["cls"]), filled(z["fine"]), pal, float(info["fine_span"])


def _grain(n, seed):
    """A ground's fine variation, n x n: about +-4 % over a few metres and +-3 % pixel to pixel (no broad mottle: the
    painter's two-scale mottle and its shade blots read as a beige wash between the houses, PC check r5)."""
    rng = np.random.default_rng(seed)
    g = np.asarray(Image.fromarray((rng.random((n // 8, n // 8)) * 255).astype(np.uint8))
                   .resize((n, n), Image.BICUBIC), float) / 255 - 0.5
    return 1.0 + 0.08 * g + 0.06 * (rng.random((n, n)) - 0.5)


def _tree_shade(n, to_px, scale, rows):
    """How much each pixel of an n x n map lies in a tree's shade (0..1): a soft disc the crown's width under each
    tree in `rows` (x, z, height, radius, kind), `to_px` the map pixel of a model x, z, `scale` pixels a metre."""
    im = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(im)
    for x, z, h, r, _ in rows:
        cx, cy = to_px(x, z)
        rr = r * 0.95 * scale
        if -rr < cx < n + rr and -rr < cy < n + rr:
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(1.2 * scale)), float) / 255


def _draw_mapped(d, ways, to_px, scale):
    """The map's own paint (car parks, paths, roads and roofs, as the MCG painter draws them) on draw `d`, pixels
    from `to_px`, `scale` pixels a metre. Returns nothing; the caller's mask draw gets the same shapes."""
    areas = [(t, p) for t, p in ways if len(p) > 2 and p[0] == p[-1] and t.get("amenity") == "parking"
             and t.get("parking") != "underground"]
    for t, p in areas:
        d.polygon([to_px(*S.model_xz(*q)) for q in p], fill=S.PARKING)
    order = sorted([(S.WIDTH.get(t.get("highway"), 0), t, p) for t, p in ways
                    if t.get("highway") in S.WIDTH and len(p) > 1 and t.get("tunnel") != "yes"
                    and t.get("area") != "yes" and t.get("layer", "0") in ("0", "-1")], key=lambda a: a[0])
    for w, t, p in order:
        fill = S.PATH if w < 4.6 and t.get("highway") != "service" else S.ASPHALT
        if t.get("highway") == "service" and t.get("service") == "parking_aisle":
            fill = S.PARKING
        d.line([to_px(*S.model_xz(*q)) for q in p], fill=fill, width=max(1, int(round(w * scale))), joint="curve")
    for t, p in ways:
        if "building" in t and len(p) > 2 and t.get("building") not in ("roof",):
            d.polygon([to_px(*S.model_xz(*q)) for q in p], fill=S.ROOF)


def ge_ground(arr, ways, sea, foot, rows):
    """The open ground as Google Earth shows it (ge_ground.py, ge_ground.npz): lawn, dry grass, bare earth,
    paving and courts each in its own measured colour with a fine grain, and the shade of each tree in `rows`.
    Roads, buildings, car parks, the sea and the stadium keep the map's own paint; under the canopy and on roofs or
    shadow the ground takes the nearest class round it."""
    from scipy import ndimage
    got = _ground_classes()
    if got is None:
        return arr
    cls, _, pal, _ = got
    raw = np.load(os.path.join(HERE, "ge_ground.npz"))["cls"]
    seen = ndimage.distance_transform_edt(raw == 255) < 40          # a strip no shot saw takes the class beside it
    mapped = Image.new("L", (S.SIZE, S.SIZE)); d = ImageDraw.Draw(mapped)
    for t, p in ways:
        if len(p) < 2:
            continue
        if ("building" in t or t.get("amenity") == "parking") and len(p) > 2:
            d.polygon([S.px(*q) for q in p], fill=1)
        elif t.get("highway") in S.WIDTH and t.get("tunnel") != "yes":
            d.line([S.px(*q) for q in p], fill=1, width=max(1, int(round(S.WIDTH[t["highway"]]))))
    open_ = seen & ~np.asarray(mapped, bool) & ~sea & ~foot
    paint = pal[cls] * _grain(S.SIZE, 11)[..., None]
    shade = _tree_shade(S.SIZE, lambda x, z: (x + S.SIZE / 2, z + S.SIZE / 2), 1.0, rows)
    paint *= (1.0 - 0.45 * shade)[..., None]
    out = arr.copy()
    out[open_] = paint[open_]
    return out


def near_map(arr, ways, sea, sand, foot, rows):
    """surrounds_near.webp: the ground FINE_SPAN m a side round the middle at the fine grid's 0.375 m a pixel (the
    1 m map read as mush in close views, PC check r5). Open ground from the fine classes; roads, paths, car parks
    and roofs drawn again at this scale; the sea, the beach and the stadium's plan from the 1 m map."""
    from scipy import ndimage
    got = _ground_classes()
    if got is None:
        return None
    _, fine, pal, span = got
    n = fine.shape[0]
    step = span / n
    half = S.SIZE / 2

    def to_px(x, z):
        return ((x + span / 2) / step, (z + span / 2) / step)
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    fx = (xx + 0.5) * step - span / 2 + half - 0.5            # the 1 m map's pixel under each fine pixel's centre
    fz = (yy + 0.5) * step - span / 2 + half - 0.5
    base = np.stack([ndimage.map_coordinates(arr[..., c], [fz, fx], order=1) for c in range(3)], -1)
    soft = lambda m: ndimage.map_coordinates(m.astype(float), [fz, fx], order=1) > 0.5
    sea_n, sand_n, foot_n = soft(sea), soft(sand), soft(foot)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    _draw_mapped(ImageDraw.Draw(im), ways, to_px, 1.0 / step)
    mk = Image.new("RGB", (n, n), (0, 0, 0))
    _draw_mapped(ImageDraw.Draw(mk), ways, to_px, 1.0 / step)
    mapped = np.asarray(mk).sum(2) > 0
    out = np.asarray(im, float).copy()
    paint = pal[fine] * _grain(n, 13)[..., None]
    shade = _tree_shade(n, to_px, 1.0 / step, rows)
    paint *= (1.0 - 0.45 * shade)[..., None]
    open_ = ~mapped & ~sea_n & ~sand_n & ~foot_n
    out[open_] = paint[open_]
    out[foot_n] = base[foot_n]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def from_google_earth(buf):
    """Each building as Google Earth shows it (houses_ge.py, houses_ge.json): its roof's own colour (roofs.bin,
    linear RGB, one triple a building; a building the shots missed takes the median of the measured roofs), a
    gable where its roof is one (height -100 - eave: GroundModels._add_buildings), and a house's eave height
    where Google Earth's heights were read (heights/read.py: one storey 2.7 m, two 5.6 m, within 450 m), or a flat
    roof at its height where all five readings agree two storeys up."""
    import houses_ge as H
    got = json.load(open(os.path.join(HERE, "houses_ge.json")))
    med = np.median([e["rgb"] for e in got.values()], axis=0)
    out = buf.copy()
    rgb = []
    i = 0
    while i + 1 < len(out):
        n = int(out[i])
        pts = out[i + 2:i + 2 + 2 * n].reshape(-1, 2).astype(float)
        e = got.get(H.key(pts), {})
        rgb += list(e.get("rgb", med))
        if out[i + 1] < 0:
            eave = -float(out[i + 1])
            if "eave" in e:
                eave = float(e["eave"])
            out[i + 1] = -eave - (100.0 if e.get("kind") == "gable" else 0.0)
            if e.get("kind") == "flat":
                out[i + 1] = eave                    # a flat roof that high (heights/read.py: townhouses)
        i += 2 + 2 * n
    return out, np.array(rgb, "<f4")


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
