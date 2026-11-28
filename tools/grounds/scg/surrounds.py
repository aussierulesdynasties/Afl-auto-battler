"""The SCG's surroundings from OpenStreetMap (SCG rebuild to the MCG standard, stage 6).

Paints the ground round the Sydney Cricket Ground, 2 km a side at 1 m a pixel: Moore Park's dry grass,
Tramway Oval, the golf course and Centennial Park's edge, the Entertainment Quarter, Allianz Stadium's
concourse, the streets and the footprint of every building. Lists every mapped tree, fills the parks to
Google Earth's density, and extrudes the buildings to their mapped heights, as
tools/grounds/marvel/surrounds.py does for Marvel (docs/MCG_STANDARD.md, Surroundings).

    python3 tools/grounds/scg/surrounds.py [tile.osm ...]

With no file it fetches the area in nine tiles (the API's limit) from the OpenStreetMap API. Writes
assets/grounds/scg/surrounds.webp, trees.bin (x, z, height, canopy radius, shade per tree) and
buildings.bin (per building: point count, height, then x, z of each footprint point), all float32 in
the model's metres: x east, z south, the model's 0, 0 at the middle of the map.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg")
# The model's 0, 0 (x east, y north), solved from the OpenStreetMap nodes the model was measured round
# (.claude/review/scg/build/osm/geo.json on branch claude/inspiring-heisenberg-a3f33c, residual < 1 mm).
LAT0, LON0 = -33.8916, 151.2248
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
BBOX = (LON0 - 0.0115, LAT0 - 0.0095, LON0 + 0.0115, LAT0 + 0.0095)   # lon/lat, about 2.1 x 2.1 km
RELATIONS = []
SIZE = 2048            # pixels a side, 1 m each, centred on the model's 0, 0
STADIUM_WAY = "387975057"   # the SCG's leisure=stadium outline
# Inside the model's own concourse nothing is planted: the model draws it.
MODEL_R = 150.0

# Colours: Google Earth's over Moore Park in summer, for the same match light as Marvel's map
# (GroundModels SURROUNDS tint): dry yellow-brown parkland, greener irrigated ovals, dark gum canopies.
BASE = (150, 150, 128)         # Paddington and Moore Park's streets of houses between mapped areas
LAWN = (150, 146, 96)          # Moore Park's open grass, dry in summer
GOLF = (118, 140, 78)          # the golf course's fairways
PITCH = (112, 146, 70)         # irrigated ovals and fields (Tramway Oval, the Showground)
SCRUB = (137, 137, 100)
WETLAND = (105, 119, 82)
SAND = (221, 220, 176)
SHOWRING_WAY = "212255119"     # OpenStreetMap's outline of the Entertainment Quarter's Showring
SHOWRING_RING = 6
ASPHALT = (140, 134, 124)      # Google Earth's roads here are warm light grey (150, 142, 132): the match light cools and darkens the map about a tenth
PARKING = (138, 134, 126)
PATH = (172, 164, 148)         # Moore Park's paths in Google Earth (145, 135, 128), a touch lighter than the roads
PAVED = (156, 147, 138)        # concrete plazas and forecourts: Google Earth's (155-161, 144-148, 130-138)
PLAZA = (190, 160, 140)
CONCOURSE = (150, 140, 126)    # the SCG's concourse and forecourts: warm grey concrete in Google Earth
BALLAST = (126, 128, 118)
RAIL = (80, 76, 70)
ROOF = (140, 142, 138)
WATER = (62, 79, 76)
URBAN = (150, 150, 128)
WOOD = (72, 92, 54)

WIDTH = {"motorway": 15, "trunk": 14, "primary": 13, "secondary": 11, "tertiary": 9,
         "residential": 7, "unclassified": 6, "service": 4.5, "living_street": 5,
         "pedestrian": 4, "footway": 2.6, "path": 2.4, "cycleway": 2.6, "steps": 2.5, "track": 3,
         "motorway_link": 7, "trunk_link": 7, "primary_link": 7, "tertiary_link": 6}


def xy(lat, lon):
    """Metres east and north of the model's 0, 0."""
    return ((lon - LON0) * KX, (lat - LAT0) * KY)


def model_xz(e, n):
    return e, -n


def px(e, n):
    x, z = model_xz(e, n)
    return (x + SIZE / 2, z + SIZE / 2)


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())


def _nodes(root, into):
    for n in root.findall("node"):
        into[n.get("id")] = (xy(float(n.get("lat")), float(n.get("lon"))),
                             {t.get("k"): t.get("v") for t in n.findall("tag")})


def load(path, rel_paths):
    roots = [ET.parse(path).getroot()] + [ET.parse(p).getroot() for p in rel_paths]
    nodes = {}
    for r in roots:
        _nodes(r, nodes)
    trees = [e for e, t in nodes.values() if t.get("natural") == "tree"]   # nodes is keyed by id: no repeats
    ways, by_id, seen = [], {}, set()
    for r in roots:
        for w in r.findall("way"):
            pts = [nodes[nd.get("ref")][0] for nd in w.findall("nd") if nd.get("ref") in nodes]
            by_id[w.get("id")] = pts
            if w.get("id") in seen:
                continue
            seen.add(w.get("id"))
            tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
            tags["_id"] = w.get("id")
            ways.append((tags, pts))
    done = set()
    for r in roots:
        for rel in r.findall("relation"):
            tags = {t.get("k"): t.get("v") for t in rel.findall("tag")}
            if tags.get("type") != "multipolygon" or rel.get("id") in done:
                continue
            done.add(rel.get("id"))
            for role in ("outer", "inner"):
                segs = [by_id[m.get("ref")] for m in rel.findall("member")
                        if m.get("type") == "way" and m.get("role") == role and by_id.get(m.get("ref"))]
                for ring in _rings(segs):
                    t = dict(tags) if role == "outer" else {"_hole": "yes"}
                    ways.append((t, ring))
    return trees, ways


def _rings(segs):
    """Joins a multipolygon's member ways into closed rings by their end points."""
    segs = [list(s) for s in segs if len(s) > 1]
    out = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[::-1][1:]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(i)
                changed = True
                break
        if len(ring) > 3:
            out.append(ring if ring[0] == ring[-1] else ring + [ring[0]])
    return out


def area_colour(t):
    if t.get("_hole"):
        return None
    if t.get("natural") == "water" or t.get("waterway") == "riverbank" or t.get("leisure") == "swimming_pool":
        return WATER
    if t.get("natural") == "wetland":
        return WETLAND
    if t.get("natural") in ("sand", "beach"):
        return SAND
    if t.get("amenity") == "parking" and t.get("parking") not in ("underground", "multi-storey"):
        return PARKING
    if t.get("leisure") == "pitch":
        return PITCH
    if t.get("leisure") == "golf_course" or t.get("golf") in ("fairway", "green", "tee"):
        return GOLF
    if t.get("natural") == "wood" or t.get("landuse") == "forest":
        return WOOD
    if t.get("natural") in ("scrub", "heath", "grassland"):
        return SCRUB
    if t.get("landuse") in ("grass", "recreation_ground") or t.get("natural") == "grass" \
            or t.get("leisure") in ("garden", "park"):
        return LAWN
    if t.get("landuse") == "railway":
        return BALLAST
    if t.get("landuse") in ("residential",):
        return URBAN
    if t.get("landuse") in ("retail", "commercial", "industrial", "construction") or t.get("area:highway"):
        return PAVED
    if t.get("highway") == "pedestrian" and t.get("area") == "yes":
        return PAVED
    if t.get("place") == "square" or t.get("leisure") == "stadium" and t.get("_id") != STADIUM_WAY:
        return PAVED
    return None


def _area(p):
    a = np.array(p)
    return 0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])


def _inside(pt, poly):
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def stadium_ring(ways):
    for t, p in ways:
        if t.get("_id") == STADIUM_WAY:
            return p
    return []


def paint(trees, ways):
    rng = np.random.default_rng(7)
    n1 = np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    n2 = np.asarray(Image.fromarray((rng.random((256, 256)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    mott = (n1 - 0.5) * 0.22 + (n2 - 0.5) * 0.12
    base = np.clip(np.array(BASE, float)[None, None, :] * (1.0 + mott[..., None]), 0, 255).astype(np.uint8)
    im = Image.fromarray(base, "RGB")
    d = ImageDraw.Draw(im)

    def poly(pts):
        return [px(*p) for p in pts]

    # The concourse round the stadium: concrete paving out to its footprint plus 25 m, under everything else.
    st = stadium_ring(ways)
    if st:
        c = np.mean(np.array(st[:-1]), axis=0)
        grown = [tuple(c + (np.array(p) - c) * (1.0 + 25.0 / max(1.0, np.hypot(*(np.array(p) - c))))) for p in st]
        d.polygon(poly(grown), fill=CONCOURSE)
    areas = [(t, p) for t, p in ways if len(p) > 2 and p[0] == p[-1] and (area_colour(t) or t.get("_hole"))]
    # The big ones first so the small ones sit on top; a multipolygon's holes right after their outer.
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        if t.get("_hole"):
            continue
        d.polygon(poly(p), fill=area_colour(t))
    # The Entertainment Quarter's Showring: OpenStreetMap maps it only as a pedestrian area, Google Earth
    # shows a grass arena inside a paved ring about SHOWRING_RING metres wide.
    for t, p in ways:
        if t.get("_id") == SHOWRING_WAY:
            ring = Image.new("L", (SIZE, SIZE), 0)
            ImageDraw.Draw(ring).polygon(poly(p), fill=255)
            ring = ring.filter(ImageFilter.MinFilter(2 * SHOWRING_RING + 1))
            im.paste(Image.new("RGB", (SIZE, SIZE), PITCH), (0, 0), ring)
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            d.line(poly(p), fill=BALLAST, width=5, joint="curve")
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            d.line(poly(p), fill=RAIL, width=1)
    # Roads and paths; bridges are drawn in 3D (bridges.glb), so the river shows under them.
    order = sorted([(WIDTH.get(t.get("highway"), 0), t, p) for t, p in ways
                    if t.get("highway") in WIDTH and len(p) > 1 and t.get("tunnel") != "yes"
                    and t.get("bridge") is None and t.get("area") != "yes"
                    and t.get("layer", "0") in ("0", "-1")], key=lambda a: a[0])
    for w, t, p in order:
        fill = PATH if w < 4.6 and t.get("highway") != "service" else ASPHALT
        if t.get("highway") == "service" and t.get("service") == "parking_aisle":
            fill = PARKING
        d.line(poly(p), fill=fill, width=max(1, int(round(w))), joint="curve")
    for t, p in ways:
        if "building" in t and len(p) > 2 and t.get("building") not in ("roof",) and t.get("_id") != STADIUM_WAY:
            # the SCG's own stands are mapped as buildings reaching past the model's walls: under them
            # the concourse shows, not a pale roof ring round the ground
            if st and _inside(tuple(np.mean(np.array(p[:-1]), axis=0)), st):
                continue
            d.polygon(poly(p), fill=ROOF)
    arr = np.asarray(im, float)
    shade = Image.new("L", (SIZE, SIZE), 0)
    sd = ImageDraw.Draw(shade)
    for e, n, r in trees:
        x, y = px(e, n)
        sd.ellipse((x - r, y - r, x + r, y + r), fill=150)
    shade = np.asarray(shade.filter(ImageFilter.GaussianBlur(2.5)), float) / 255
    arr *= (1.0 - 0.45 * shade)[..., None]
    grain = (rng.random((SIZE, SIZE)) - 0.5) * 10
    arr += grain[..., None]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    r = np.hypot(xx - SIZE / 2, yy - SIZE / 2)
    edge = np.clip((r - 900) / 120, 0, 1)[..., None]
    arr = arr * (1 - edge) + np.array(URBAN, float) * edge
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def all_trees(mapped, ways):
    """Every mapped tree, plus trees scattered through the mapped woods (one per 90 m2) and scrub
    (one per 260 m2): (east, north, shade radius)."""
    rng = np.random.default_rng(11)
    out = [(e, n, 4.5) for e, n in mapped]
    for t, p in ways:
        dens = 90.0 if t.get("natural") == "wood" or t.get("landuse") == "forest" else \
            260.0 if t.get("natural") in ("scrub", "heath") else 0.0
        if dens == 0.0 or len(p) < 4 or p[0] != p[-1] or t.get("_hole"):
            continue
        a = np.array(p)
        lo, hi = a.min(0), a.max(0)
        k = int(abs(_area(p)) / dens)
        for _ in range(k * 3):
            if k <= 0:
                break
            q = (rng.uniform(lo[0], hi[0]), rng.uniform(lo[1], hi[1]))
            if _inside(q, p):
                out.append((q[0], q[1], 3.5))
                k -= 1
    return out


# Trees a square metre in a park's open grass once filled (Google Earth's Moore Park: rows of figs and
# gums, a canopy every 15 m or so along its avenues), never nearer than TREE_GAP to another tree or
# 3 m to a path, road or roof. As tools/grounds/mcg/surrounds.py fills Yarra Park.
PARK_DENSITY = 1.0 / 420.0
TREE_GAP = 11.0


def fill_parks(im, trees, ways):
    a = np.asarray(im, int)
    # Open grass: the lawn colours, not paths, asphalt, roofs or water.
    grass = (np.abs(a - np.array(LAWN)[None, None, :]).sum(-1) < 60) | (np.abs(a - np.array(GOLF)[None, None, :]).sum(-1) < 60)
    nog = Image.new("L", (SIZE, SIZE), 0)
    nd = ImageDraw.Draw(nog)
    for t, p in ways:
        if t.get("leisure") in ("pitch", "golf_course") or t.get("golf"):
            if len(p) > 2:
                nd.polygon([px(*q) for q in p], fill=255)
    grass &= np.asarray(nog) == 0
    clear = np.asarray(Image.fromarray((~grass * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) == 0
    rng = np.random.default_rng(23)
    have = [model_xz(*e) for e in trees]
    cell = {}

    def key(x, z):
        return (int(x // TREE_GAP), int(z // TREE_GAP))

    for x, z in have:
        cell.setdefault(key(x, z), []).append((x, z))
    added = []
    for t, p in ways:
        if t.get("leisure") not in ("park", "garden") or len(p) < 4 or t.get("_hole"):
            continue
        poly = [model_xz(*q) for q in p]
        if max(max(abs(x), abs(z)) for x, z in poly) > 950:
            continue
        mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).polygon([(x + SIZE / 2, z + SIZE / 2) for x, z in poly], fill=255)
        m = np.asarray(mask) > 0
        ys, xs = np.nonzero(m & clear)
        if len(xs) == 0:
            continue
        want = int(len(xs) * PARK_DENSITY)
        inside = sum(1 for x, z in have if 0 <= x + SIZE / 2 < SIZE and 0 <= z + SIZE / 2 < SIZE
                     and m[int(z + SIZE / 2), int(x + SIZE / 2)])
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
    return [(x, -z, 4.5) for x, z in added]


def tree_list(trees, st):
    rng = np.random.default_rng(13)
    out = []
    for e, n, _r in trees:
        x, z = model_xz(e, n)
        if (st and _inside((e, n), st)) or abs(x) > 950 or abs(z) > 950:
            continue
        # Moore Park's Moreton Bay figs and gums are big, broad trees (Google Earth: crowns 15-25 m across).
        h = rng.uniform(10.0, 19.0)
        out.append((x, z, h, h * rng.uniform(0.42, 0.58), rng.uniform(0.0, 1.0)))
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
    return {"house": 7.0, "terrace": 8.0, "garage": 3.0, "shed": 3.0, "apartments": 16.0, "residential": 12.0,
            "industrial": 7.0, "roof": 0.0, "train_station": 7.0, "hotel": 40.0}.get(t.get("building"), 8.0)


def building_list(ways, st):
    out = []
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        if t.get("_id") == STADIUM_WAY:
            continue
        a = np.array(p[:-1])
        if st and _inside(tuple(a.mean(0)), st):
            continue
        pts = [model_xz(*q) for q in p[:-1]]
        if max(max(abs(x), abs(z)) for x, z in pts) > 950:
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
    files = sys.argv[1:]
    if not files:
        x0, y0, x1, y1 = BBOX
        for i in range(3):
            for j in range(3):
                p = "/tmp/scg_surrounds_%d%d.osm" % (i, j)
                if not os.path.exists(p):
                    fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (
                        x0 + (x1 - x0) * i / 3, y0 + (y1 - y0) * j / 3,
                        x0 + (x1 - x0) * (i + 1) / 3, y0 + (y1 - y0) * (j + 1) / 3), p)
                files.append(p)
        for r in RELATIONS:
            p = "/tmp/scg_rel_%d.osm" % r
            if not os.path.exists(p):
                fetch("https://api.openstreetmap.org/api/0.6/relation/%d/full" % r, p)
            files.append(p)
    mapped, ways = load(files[0], files[1:])
    st = stadium_ring(ways)
    trees = all_trees(mapped, ways)
    im = paint(trees, ways)
    extra = fill_parks(im, [(e, n) for e, n, _r in trees], ways)
    if extra:
        trees += extra
        im = paint(trees, ways)
    print("mapped trees", len(mapped), "park fill", len(extra))
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = tree_list(trees, st)
    t.tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, st)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
