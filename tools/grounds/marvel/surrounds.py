"""Marvel Stadium's surroundings from OpenStreetMap (Marvel rebuild to the MCG standard, stage 6).

Paints the ground round Marvel Stadium, 2 km a side at 1 m a pixel: Victoria Harbour and the Yarra, the
Southern Cross rail yards, Docklands' streets, plazas and promenades, building footprints. Lists every
mapped tree and extrudes the buildings (Docklands' and the CBD's towers to their mapped heights), as
tools/grounds/optus/surrounds.py does for Optus (docs/MCG_STANDARD.md, Surroundings).

    python3 tools/grounds/marvel/surrounds.py [tile.osm ...]

With no file it fetches the area in nine tiles (the API's limit) and the river's multipolygons from the
OpenStreetMap API. Writes assets/grounds/marvel/surrounds.webp, trees.bin (x, z, height, canopy radius, shade per tree) and
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
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "marvel")
# The model's 0, 0 (x east, y north): the middle of the pitch, OpenStreetMap way 10583685, which the
# model was measured round (.claude/review/marvel/mv/osm/geo.json).
LAT0, LON0 = -37.816495302702705, 144.9475565216216
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
BBOX = (LON0 - 0.0125, LAT0 - 0.0099, LON0 + 0.0125, LAT0 + 0.0099)   # lon/lat, about 2.2 x 2.2 km
# The Yarra and Victoria Harbour, mapped as multipolygons.
RELATIONS = [954522, 11570858]
SIZE = 2048            # pixels a side, 1 m each, centred on the model's 0, 0
STADIUM_WAY = "22971441"

# Colours: Google Earth's over Docklands, painted through the match light's measured response (GroundModels
# SURROUNDS tint 2.0, 1.4, 0.95, then about R 0.95x - 10, G 0.84x, B 0.85x on screen), so each renders as
# Google Earth shows it: dry summer grass, green irrigated lawns, the dark river.
BASE = (160, 164, 152)         # Docklands is paved and built over: the city's grey between mapped areas
LAWN = (108, 156, 70)          # the irrigated lawns: Stadium Park, Pelican Lawns, the river parks
PITCH = (102, 152, 62)
SCRUB = (137, 137, 100)
WETLAND = (105, 119, 82)
SAND = (221, 220, 176)
ASPHALT = (105, 110, 108)
PARKING = (132, 137, 132)
PATH = (216, 220, 194)
PAVED = (184, 190, 176)        # concrete plazas, promenades and the stadium's concourse
PLAZA = (206, 150, 128)        # the red-brown paving of the promenades (Harbour Esplanade, Docklands Park)
BALLAST = (147, 140, 118)
RAIL = (80, 76, 70)
ROOF = (168, 179, 174)
WATER = (62, 79, 76)
URBAN = (160, 164, 152)
WOOD = (84, 101, 59)

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
        d.polygon(poly(grown), fill=PAVED)
    areas = [(t, p) for t, p in ways if len(p) > 2 and p[0] == p[-1] and (area_colour(t) or t.get("_hole"))]
    # The big ones first so the small ones sit on top; a multipolygon's holes right after their outer.
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        if t.get("_hole"):
            continue
        d.polygon(poly(p), fill=area_colour(t))
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


def tree_list(trees, st):
    rng = np.random.default_rng(13)
    out = []
    for e, n, _r in trees:
        x, z = model_xz(e, n)
        if (st and _inside((e, n), st)) or abs(x) > 950 or abs(z) > 950:
            continue
        h = rng.uniform(7.0, 15.0)
        out.append((x, z, h, h * rng.uniform(0.3, 0.4), rng.uniform(0.0, 1.0)))
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
                p = "/tmp/marvel_surrounds_%d%d.osm" % (i, j)
                if not os.path.exists(p):
                    fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (
                        x0 + (x1 - x0) * i / 3, y0 + (y1 - y0) * j / 3,
                        x0 + (x1 - x0) * (i + 1) / 3, y0 + (y1 - y0) * (j + 1) / 3), p)
                files.append(p)
        for r in RELATIONS:
            p = "/tmp/marvel_rel_%d.osm" % r
            if not os.path.exists(p):
                fetch("https://api.openstreetmap.org/api/0.6/relation/%d/full" % r, p)
            files.append(p)
    mapped, ways = load(files[0], files[1:])
    st = stadium_ring(ways)
    trees = all_trees(mapped, ways)
    im = paint(trees, ways)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = tree_list(trees, st)
    t.tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, st)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
