"""The MCG's surroundings from OpenStreetMap (MCG flagship, stage 6).

Paints the ground round the MCG, 2 km a side at 1 m a pixel (Yarra Park's grass, paths and car parks,
the roads, the rail yards to the west and south-west, building footprints, water), and lists every
tree OpenStreetMap maps there (Yarra Park's elms and gums, about 2,400) for GroundModels to stand up.

    python3 tools/grounds/mcg/surrounds.py [map.osm]

With no file it fetches the area from the OpenStreetMap API. Writes assets/grounds/mcg/surrounds.webp
assets/grounds/mcg/trees.bin (x, z, height, canopy radius, shade per tree) and
assets/grounds/mcg/buildings.bin (per building: point count, height, then x, z for each point of its
footprint), all float32 in model metres: x east, z south, the field's centre at 0, 0. Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "mcg")
BBOX = (144.972, -37.827, 144.994, -37.812)   # lon/lat, about 1.9 x 1.7 km round the ground
LAT0, LON0 = -37.81977, 144.98316
# The AFL pitch's centre in OpenStreetMap is 25.3 m east and 23.5 m south of LAT0/LON0: the model's 0, 0.
PITCH_E, PITCH_N = 25.3, -23.5
SIZE = 2048            # pixels a side, 1 m each, centred on the field
# Inside the model's own plaza nothing is painted: the model draws it.
MODEL_R = 150.0

BASE = (116, 124, 82)          # Yarra Park's dry summer grass, as Google Earth shows it
LAWN = (108, 124, 76)
PITCH = (92, 124, 62)
ASPHALT = (96, 96, 96)
PARKING = (112, 110, 106)
PATH = (170, 164, 148)
PAVED = (160, 156, 146)
BALLAST = (120, 110, 98)
RAIL = (70, 62, 56)
ROOF = (146, 144, 140)
WATER = (70, 92, 96)
URBAN = (118, 120, 108)        # houses and their gardens (East Melbourne, Richmond)
WOOD = (78, 98, 56)

WIDTH = {"motorway": 16, "trunk": 14, "primary": 13, "secondary": 11, "tertiary": 9,
         "residential": 7, "unclassified": 6, "service": 4.5, "living_street": 5,
         "pedestrian": 4, "footway": 2.6, "path": 2.0, "cycleway": 2.6, "steps": 2.5, "track": 3}


def en(lat, lon):
    return ((lon - LON0) * math.cos(math.radians(LAT0)) * 111320.0, (lat - LAT0) * 110574.0)


def model_xz(e, n):
    return e - PITCH_E, -(n - PITCH_N)


def px(e, n):
    x, z = model_xz(e, n)
    return (x + SIZE / 2, z + SIZE / 2)


def fetch(path):
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % BBOX
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def load(path):
    root = ET.parse(path).getroot()
    nodes, trees, ways = {}, [], []
    for n in root.findall("node"):
        e = en(float(n.get("lat")), float(n.get("lon")))
        nodes[n.get("id")] = e
        tags = {t.get("k"): t.get("v") for t in n.findall("tag")}
        if tags.get("natural") == "tree":
            trees.append(e)
    by_id = {}
    for w in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
        pts = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
        by_id[w.get("id")] = pts
        ways.append((tags, pts))
    for r in root.findall("relation"):
        tags = {t.get("k"): t.get("v") for t in r.findall("tag")}
        if tags.get("type") != "multipolygon":
            continue
        for m in r.findall("member"):
            if m.get("type") == "way" and m.get("role") == "outer" and m.get("ref") in by_id:
                ways.append((tags, by_id[m.get("ref")]))
    return trees, ways


def area_colour(t):
    if t.get("natural") == "water" or t.get("waterway") == "riverbank" or t.get("leisure") == "swimming_pool":
        return WATER
    if t.get("amenity") == "parking" and t.get("parking") not in ("underground",):
        return PARKING
    if t.get("leisure") == "pitch":
        return PITCH
    if t.get("natural") == "wood" or t.get("landuse") == "forest":
        return WOOD
    if t.get("landuse") in ("grass",) or t.get("leisure") in ("garden", "park"):
        return LAWN
    if t.get("landuse") == "railway":
        return BALLAST
    if t.get("landuse") in ("residential",):
        return URBAN
    if t.get("landuse") in ("retail", "commercial", "construction") or t.get("area:highway"):
        return PAVED
    if t.get("highway") == "pedestrian" and t.get("area") == "yes":
        return PAVED
    return None


def paint(trees, ways):
    rng = np.random.default_rng(7)
    # Base: grass, mottled at two scales so it does not read as a flat sheet.
    n1 = np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    n2 = np.asarray(Image.fromarray((rng.random((256, 256)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    mott = (n1 - 0.5) * 0.22 + (n2 - 0.5) * 0.12
    base = np.clip(np.array(BASE, float)[None, None, :] * (1.0 + mott[..., None]), 0, 255).astype(np.uint8)
    im = Image.fromarray(base, "RGB")
    d = ImageDraw.Draw(im)

    def poly(pts):
        return [px(*p) for p in pts]

    # Areas, the big ones first so the small ones sit on top.
    areas = [(t, p) for t, p in ways if len(p) > 2 and p[0] == p[-1] and area_colour(t)]
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        d.polygon(poly(p), fill=area_colour(t))
    # Rail: ballast under every track, then the two rails.
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            w = 4.4 if t["railway"] == "rail" else 3.2
            d.line(poly(p), fill=BALLAST if t["railway"] == "rail" else ASPHALT, width=int(round(w)), joint="curve")
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            d.line(poly(p), fill=RAIL, width=1)
    # Roads and paths, the small ones first so a road runs over the path that meets it.
    order = sorted([(WIDTH.get(t.get("highway"), 0), t, p) for t, p in ways
                    if t.get("highway") in WIDTH and len(p) > 1 and t.get("tunnel") != "yes"
                    and t.get("area") != "yes" and t.get("layer", "0") in ("0", "-1")], key=lambda a: a[0])
    for w, t, p in order:
        fill = PATH if w < 4.6 and t.get("highway") != "service" else ASPHALT
        if t.get("highway") == "service" and t.get("service") == "parking_aisle":
            fill = PARKING
        d.line(poly(p), fill=fill, width=max(1, int(round(w))), joint="curve")
    # Buildings: flat roofs from above.
    for t, p in ways:
        if "building" in t and len(p) > 2 and t.get("building") not in ("roof",):
            d.polygon(poly(p), fill=ROOF)
    # The parks' unmapped trees: OpenStreetMap has only some of them (Yarra Park reads half as
    # dense as Google Earth), so each park is filled to PARK_DENSITY on its open grass.
    trees = trees + fill_parks(im, trees, ways)
    # Under every tree its canopy's shade (the 3D tree stands on it): darker and browner, the bare
    # ground under Yarra Park's elms and gums.
    arr = np.asarray(im, float)
    shade = Image.new("L", (SIZE, SIZE), 0)
    sd = ImageDraw.Draw(shade)
    for e, n in trees:
        x, y = px(e, n)
        r = 6.0
        sd.ellipse((x - r, y - r, x + r, y + r), fill=150)
    shade = np.asarray(shade.filter(ImageFilter.GaussianBlur(2.5)), float) / 255
    arr = arr * (1.0 - 0.5 * shade)[..., None] + np.array([18.0, 6.0, -4.0]) * shade[..., None]
    # Fine grain over everything. No fade to a town grey at the edge: join_band.py blends the outer 60 m into the
    # backdrop's own ground (run `join_band.py apply <ground>` after this script).
    grain = (rng.random((SIZE, SIZE)) - 0.5) * 10
    arr += grain[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB"), trees


# Trees a square metre in a park's open grass once filled (Google Earth's Yarra Park: a canopy
# every 14 m or so), never nearer than TREE_GAP to another tree or 3 m to a path, road or roof.
PARK_DENSITY = 1.0 / 190.0
TREE_GAP = 9.5


def fill_parks(im, trees, ways):
    a = np.asarray(im, int)
    # Open grass: green over blue (paths, asphalt, roofs, ballast and water are grey or brown).
    grass = (a[..., 1] - a[..., 2] > 40) & (a[..., 1] >= a[..., 0] - 30)
    nog = Image.new("L", (SIZE, SIZE), 0)
    nd = ImageDraw.Draw(nog)
    for t, p in ways:
        if t.get("leisure") == "pitch" and len(p) > 2:
            nd.polygon([px(*q) for q in p], fill=255)
    grass &= np.asarray(nog) == 0
    # 3 m clear of anything that is not grass.
    clear = np.asarray(Image.fromarray((~grass * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) == 0
    rng = np.random.default_rng(23)
    have = np.array([model_xz(*e) for e in trees]) if trees else np.zeros((0, 2))
    cell = {}

    def key(x, z):
        return (int(x // TREE_GAP), int(z // TREE_GAP))

    for x, z in have:
        cell.setdefault(key(x, z), []).append((x, z))
    added = []
    for t, p in ways:
        if t.get("leisure") not in ("park", "garden") or len(p) < 4:
            continue
        poly = [model_xz(*q) for q in p]
        if max(max(abs(x), abs(z)) for x, z in poly) > 950:
            continue
        mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).polygon([(x + SIZE / 2, z + SIZE / 2) for x, z in poly], fill=255)
        ys, xs = np.nonzero((np.asarray(mask) > 0) & clear)
        if len(xs) == 0:
            continue
        want = int(len(xs) * PARK_DENSITY)
        inside = sum(1 for x, z in have if mask.getpixel((int(x + SIZE / 2), int(z + SIZE / 2))) if 0 <= x + SIZE / 2 < SIZE and 0 <= z + SIZE / 2 < SIZE)
        for _ in range(want * 12):
            if inside >= want:
                break
            k = rng.integers(len(xs))
            x, z = xs[k] - SIZE / 2 + rng.random(), ys[k] - SIZE / 2 + rng.random()
            if math.hypot(x, z) < MODEL_R + 10:
                continue
            cx, cz = key(x, z)
            near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cz + j), [])]
            if any((qx - x) ** 2 + (qz - z) ** 2 < TREE_GAP ** 2 for qx, qz in near):
                continue
            cell.setdefault((cx, cz), []).append((x, z))
            added.append((x, z))
            inside += 1
    # Back to east/north metres, as the mapped trees are.
    return [(x + PITCH_E, -z + PITCH_N) for x, z in added]


def _area(p):
    a = np.array(p)
    return 0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])


def tree_list(trees):
    rng = np.random.default_rng(11)
    out = []
    for e, n in trees:
        x, z = model_xz(e, n)
        if math.hypot(x, z) < MODEL_R or abs(x) > 950 or abs(z) > 950:
            continue
        h = rng.uniform(10.0, 18.0)
        out.append((x, z, h, h * rng.uniform(0.42, 0.55), rng.uniform(0.0, 1.0)))
    return np.array(out, "<f4")


def building_height(t):
    try:
        return float(t["height"].replace("m", "").strip())
    except (KeyError, ValueError):
        pass
    try:
        return float(t["building:levels"]) * 3.2 + 1.0
    except (KeyError, ValueError):
        pass
    return {"house": 7.0, "terrace": 8.0, "garage": 3.0, "shed": 3.0, "apartments": 16.0,
            "industrial": 7.0, "roof": 0.0, "train_station": 7.0}.get(t.get("building"), 9.0)


def building_list(ways):
    out = []
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        pts = [model_xz(*q) for q in p[:-1]]
        if min(math.hypot(x, z) for x, z in pts) < 185.0 or max(max(abs(x), abs(z)) for x, z in pts) > 950:
            continue
        h = building_height(t)
        if h < 2.5:
            continue
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    return np.array(out, "<f4")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mcg_surrounds.osm"
    if not os.path.exists(path):
        fetch(path)
    trees, ways = load(path)
    im, trees = paint(trees, ways)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = tree_list(trees)
    t.tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
