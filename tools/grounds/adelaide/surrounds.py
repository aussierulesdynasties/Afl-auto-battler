"""Adelaide Oval's surroundings from OpenStreetMap (Adelaide to the MCG standard, stage 6).

Paints the ground round Adelaide Oval, 2 km a side at 1 m a pixel: the River Torrens and Torrens Lake,
the North Adelaide parklands (Pennington Gardens, Creswell Gardens, Adelaide Oval No. 2, the tennis
courts), the Riverbank and Festival Plaza, the roads and paths, building footprints. Lists every mapped
tree (Adelaide maps its park trees well: about 3,500 here) and extrudes the buildings, the CBD towers
out past the map's edge included, as tools/grounds/optus/surrounds.py does for Optus (docs/MCG_STANDARD.md,
Surroundings).

    python3 tools/grounds/adelaide/surrounds.py [map.osm] [more.osm ...]

With no file it fetches the area, the river's multipolygon and four CBD tiles (buildings only) from the
OpenStreetMap API. Writes assets/grounds/adelaide/surrounds.webp, trees.bin (x, z, height, canopy radius,
shade per tree) and buildings.bin (per building: point count, height, then x, z of each footprint point),
all float32 in the model's metres: x east, z south, the model's 0, 0 (gen.py's OSM origin) at the middle
of the map. Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "adelaide")
BBOX = (138.5842, -34.9248, 138.6083, -34.9062)   # lon/lat, about 2.2 x 2.1 km round the ground
# The CBD south of the river, past the map's edge: its towers stand on the skyline from the stands.
CBD_TILES = [(138.5900, -34.9330, 138.6000, -34.9248), (138.6000, -34.9330, 138.6100, -34.9248),
             (138.5900, -34.9400, 138.6000, -34.9330), (138.6000, -34.9400, 138.6100, -34.9330)]
BUILD_R = 1700.0       # buildings out to here (the map itself stops at 1,024 m)
# The model's 0, 0 (x east, y north): gen.py's origin, the centroid of the oval's boundary (OSM way 4681536).
LAT0, LON0 = -34.915489777922076, 138.59627692467532
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
# River Torrens' multipolygon (Torrens Lake is a way in the main map).
RELATIONS = [73256]
SIZE = 2048            # pixels a side, 1 m each, centred on the model's 0, 0
# The near map (surrounds_near.webp): the precinct and the parkland next to the stands at 4 pixels a metre, 512 m a
# side, so the concourse, kerbs and paths stay sharp from a seat or the ground's own footpath (director fault 11:
# the far map's 1 m pixels smeared there). GroundModels draws it out to 254 m and the far map beyond.
NEAR_SIZE, NEAR_SPAN = 2048, 512.0
# What paint() draws at: pixels a side and metres a pixel (set per map by paint()).
_PX = {"size": SIZE, "ppm": 1.0}
STADIUM_WAY = "268922032"

# Colours: Google Earth's over the North Adelaide parklands in late spring, painted for the match light with no
# tint (GroundModels SURROUNDS "adelaide"): irrigated green lawns and ovals, the drier parkland grass between
# them, dark gum canopies, pale concrete round the ground, the dark green-brown Torrens.
BASE = (112, 135, 80)          # parkland grass between the lawns
LAWN = (100, 140, 72)          # irrigated lawns: Pennington and Creswell Gardens, Elder Park, the river banks
PITCH = (96, 138, 66)          # the ovals (Adelaide Oval No. 2, the Park 12 and 26 grounds)
SCRUB = (118, 124, 86)
WETLAND = (96, 112, 76)
SAND = (200, 196, 168)
ASPHALT = (92, 94, 96)
PARKING = (118, 118, 116)
PATH = (188, 184, 170)
PAVED = (168, 166, 158)        # the concourse round the ground, Festival Plaza, the Riverbank
PLAZA = PAVED
BALLAST = (120, 112, 98)
RAIL = (70, 64, 58)
ROOF = (150, 150, 146)
WATER = (58, 74, 70)
URBAN = (128, 130, 118)
WOOD = (70, 92, 52)
TENNIS = (62, 98, 140)          # the blue hard courts west of the ground

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
    k = _PX["ppm"]
    return (x * k + _PX["size"] / 2, z * k + _PX["size"] / 2)


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
    trees = [e for e, t in nodes.values() if t.get("natural") == "tree"]
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
    if t.get("leisure") == "golf_course":   # North Adelaide's fairways (OSM also tags it a construction site)
        return LAWN
    if t.get("natural") == "water" or t.get("waterway") == "riverbank" or t.get("leisure") == "swimming_pool":
        return WATER
    if t.get("natural") == "wetland":
        return WETLAND
    if t.get("natural") in ("sand", "beach"):
        return SAND
    if t.get("amenity") == "parking" and t.get("parking") not in ("underground", "multi-storey"):
        return PARKING
    if t.get("leisure") == "pitch" and t.get("sport") == "tennis":
        return TENNIS
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


def osm_stadium(ways):
    for t, p in ways:
        if t.get("_id") == STADIUM_WAY:
            return p
    return []


def stadium_ring(ways):
    """The model's own footprint (east, north), not OSM's stadium outline: OSM's takes in the whole precinct, its
    trees and the outbuildings the model leaves to the map. The convex hull of every model vertex over 1 m (the
    light towers left out), grown 4 m, so no tree or building pokes through a stand or roof."""
    import glob
    from scipy.spatial import ConvexHull
    model = os.path.join(ROOT, "..", "..", "..", ".claude", "review", "adelaide", "model")
    pts = []
    for f in glob.glob(os.path.join(model, "*.ply")):
        if os.path.basename(f) in ("ground.ply", "towers.ply") or os.path.basename(f).startswith("seats_"):
            continue
        lines = open(f, errors="ignore").read().split("\n")
        h = lines.index("end_header")
        nv = int([ln for ln in lines[:h] if ln.startswith("element vertex")][0].split()[2])
        a = np.array([[float(x) for x in ln.split()[:3]] for ln in lines[h + 1:h + 1 + nv]])
        pts.append(a[a[:, 2] > 1.0, :2])
    a = np.concatenate(pts)
    hull = a[ConvexHull(a).vertices]
    c = hull.mean(0)
    grown = [tuple(c + (q - c) * (1.0 + 4.0 / np.hypot(*(q - c)))) for q in hull]
    return grown + [grown[0]]


def paint(trees, ways, size=SIZE, span=float(SIZE)):
    """the map `span` m a side round the model's 0, 0 at `size` pixels. The broad mottle is the far map's own field,
    cut out and enlarged for the near map, so the two meet without a seam"""
    rng = np.random.default_rng(7)
    n1 = np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    n2 = np.asarray(Image.fromarray((rng.random((256, 256)) * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC), float) / 255
    mott = (n1 - 0.5) * 0.22 + (n2 - 0.5) * 0.12
    if size != SIZE or span != SIZE:
        a = int(round(SIZE / 2 - span / 2)); b = int(round(SIZE / 2 + span / 2))
        mott = np.asarray(Image.fromarray(mott[a:b, a:b].astype(np.float32), "F").resize((size, size), Image.BICUBIC), float)
    _PX["size"], _PX["ppm"] = size, size / span
    k = _PX["ppm"]
    base = np.clip(np.array(BASE, float)[None, None, :] * (1.0 + mott[..., None]), 0, 255).astype(np.uint8)
    im = Image.fromarray(base, "RGB")
    d = ImageDraw.Draw(im)

    def poly(pts):
        return [px(*p) for p in pts]

    # The stadium's precinct (OSM's leisure=stadium outline): pale concrete and pavers to its fence, under the
    # model's own concourse.
    st = osm_stadium(ways)
    if st:
        d.polygon(poly(st), fill=PAVED)
    areas = [(t, p) for t, p in ways if len(p) > 2 and p[0] == p[-1] and (area_colour(t) or t.get("_hole"))]
    # The big ones first so the small ones sit on top; a multipolygon's holes right after their outer.
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        if t.get("_hole"):
            continue
        d.polygon(poly(p), fill=area_colour(t))
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            d.line(poly(p), fill=BALLAST, width=max(1, int(round(5 * k))), joint="curve")
    for t, p in ways:
        if t.get("railway") in ("rail", "light_rail", "tram") and len(p) > 1 and t.get("tunnel") != "yes":
            d.line(poly(p), fill=RAIL, width=max(1, int(round(1 * k))))
    # Roads and paths; bridges are drawn in 3D (bridges.glb), so the river shows under them.
    order = sorted([(WIDTH.get(t.get("highway"), 0), t, p) for t, p in ways
                    if t.get("highway") in WIDTH and len(p) > 1 and t.get("tunnel") != "yes"
                    and t.get("bridge") is None and t.get("area") != "yes"
                    and t.get("layer", "0") in ("0", "-1")], key=lambda a: a[0])
    for w, t, p in order:
        fill = PATH if w < 4.6 and t.get("highway") != "service" else ASPHALT
        if t.get("highway") == "service" and t.get("service") == "parking_aisle":
            fill = PARKING
        d.line(poly(p), fill=fill, width=max(1, int(round(w * k))), joint="curve")
    for t, p in ways:
        if "building" in t and len(p) > 2 and t.get("building") not in ("roof",) and t.get("_id") != STADIUM_WAY:
            d.polygon(poly(p), fill=ROOF)
    arr = np.asarray(im, float)
    if k >= 2:   # the near map: the concourse's paving slabs (1.2 m, a tone each, faint joints) where it is paved
        pav = np.all(arr == np.array(PAVED, float), axis=-1)
        yy, xx = np.mgrid[0:size, 0:size]
        slab = 1.2 * k
        tone = rng.random((int(size / slab) + 2, int(size / slab) + 2))
        sx, sy = (xx / slab).astype(int), (yy / slab).astype(int)
        f = 1.0 + (tone[sy, sx] - 0.5) * 0.06
        joint = ((xx % slab) < 1.0) | ((yy % slab) < 1.0)
        f = np.where(joint, 0.9, f)
        arr = np.where(pav[..., None], arr * f[..., None], arr)
    shade = Image.new("L", (size, size), 0)
    sd = ImageDraw.Draw(shade)
    for e, n, r in trees:
        x, y = px(e, n)
        sd.ellipse((x - r * k, y - r * k, x + r * k, y + r * k), fill=150)
    shade = np.asarray(shade.filter(ImageFilter.GaussianBlur(2.5 * k)), float) / 255
    arr *= (1.0 - 0.45 * shade)[..., None]
    grain = (rng.random((size, size)) - 0.5) * 10
    arr += grain[..., None]
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - size / 2, yy - size / 2) / k
    edge = np.clip((r - 900) / 120, 0, 1)[..., None]
    arr = arr * (1 - edge) + np.array(URBAN, float) * edge
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# Trees a square metre in a park's open grass once filled (Google Earth's parklands: a canopy every 16 m or so
# outside the ovals), never nearer than TREE_GAP to another tree; never on a pitch, path, road or roof.
PARK_DENSITY = 1.0 / 260.0
TREE_GAP = 9.0


def fill_parks(im, have, ways, hull):
    a = np.asarray(im, int)
    grass = (a[..., 1] - a[..., 2] > 40) & (a[..., 1] >= a[..., 0])
    nog = Image.new("L", (SIZE, SIZE), 0)
    nd = ImageDraw.Draw(nog)
    for t, p in ways:
        if t.get("leisure") in ("pitch", "golf_course") and len(p) > 2:
            nd.polygon([px(*q) for q in p], fill=255)
    if hull:
        nd.polygon([px(*q) for q in hull], fill=255)
    grass &= np.asarray(nog) == 0
    clear = np.asarray(Image.fromarray((~grass * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))) == 0
    rng = np.random.default_rng(23)
    cell = {}

    def key(e, n):
        return (int(e // TREE_GAP), int(n // TREE_GAP))

    for e, n, _r in have:
        cell.setdefault(key(e, n), []).append((e, n))
    added = []
    for t, p in ways:
        if t.get("leisure") not in ("park", "garden") or len(p) < 4 or p[0] != p[-1]:
            continue
        # Park 26 holds the ground itself and its open ovals and lawns (Adelaide Oval No. 2, the practice
        # fields): Google Earth shows them open, so only the other parks are filled.
        if _inside((0.0, 0.0), p):
            continue
        mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).polygon([px(*q) for q in p], fill=255)
        ys, xs = np.nonzero((np.asarray(mask) > 0) & clear)
        if len(xs) == 0:
            continue
        want = int(len(xs) * PARK_DENSITY)
        got = 0
        for _ in range(want * 10):
            if got >= want:
                break
            k = rng.integers(len(xs))
            e, n = xs[k] - SIZE / 2 + rng.random(), -(ys[k] - SIZE / 2 + rng.random())
            if math.hypot(e, n) > 1000:
                continue
            ce, cn = key(e, n)
            near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((ce + i, cn + j), [])]
            if any((qe - e) ** 2 + (qn - n) ** 2 < TREE_GAP ** 2 for qe, qn in near):
                continue
            cell.setdefault((ce, cn), []).append((e, n))
            added.append((e, n, 4.5))
            got += 1
    return added


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
        h = rng.uniform(9.0, 18.0)      # river red gums and planes: broad crowns
        out.append((x, z, h, h * rng.uniform(0.38, 0.5), rng.uniform(0.0, 1.0)))
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


NAMED = {"red": (150, 70, 56), "white": (232, 230, 224), "silver": (190, 192, 194), "grey": (150, 150, 150),
         "gray": (150, 150, 150), "black": (50, 50, 52), "brown": (120, 84, 60), "green": (90, 120, 90),
         "beige": (214, 200, 170), "yellow": (220, 200, 120), "blue": (90, 110, 140)}
# Untagged roofs round North Adelaide (Google Earth): terracotta tile, grey and pale galvanised iron on houses;
# pale membrane and grey metal on the big flat roofs.
HOUSE_ROOFS = [(150, 78, 60), (128, 70, 58), (120, 122, 124), (168, 168, 164), (96, 96, 98)]
FLAT_ROOFS = [(196, 196, 192), (170, 170, 168), (150, 152, 152), (214, 212, 206)]
HOUSE_WALLS = [(214, 200, 176), (196, 150, 118), (224, 218, 204), (176, 120, 92)]
CITY_WALLS = [(200, 200, 196), (168, 176, 182), (214, 210, 200), (140, 150, 160), (186, 176, 160)]


def _colour(v):
    if not v:
        return None
    v = v.strip().lower()
    if v.startswith("#") and len(v) == 7:
        return tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
    return NAMED.get(v)


def building_list(ways, st):
    """The footprints (as GroundModels reads them) and, in the same order, each one's wall and roof colour
    (6 bytes: OSM building:colour / roof:colour where mapped, else a palette by kind)."""
    out, cols = [], []
    rng = np.random.default_rng(5)
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        if t.get("_id") == STADIUM_WAY:
            continue
        a = np.array(p[:-1])
        if st and _inside(tuple(a.mean(0)), st):
            continue
        pts = [model_xz(*q) for q in p[:-1]]
        if min(math.hypot(x, z) for x, z in pts) > BUILD_R:
            continue
        h = building_height(t)
        if h < 2.5:
            continue
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
        house = t.get("building") in ("house", "terrace", "detached", "semidetached_house", "garage", "shed") or h < 9
        wall = _colour(t.get("building:colour")) or (HOUSE_WALLS if house else CITY_WALLS)[rng.integers(4 if house else 5)]
        roof = _colour(t.get("roof:colour")) or (HOUSE_ROOFS if house else FLAT_ROOFS)[rng.integers(5 if house else 4)]
        cols += list(wall) + list(roof)
    return np.array(out, "<f4"), np.array(cols, np.uint8)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/adelaide_surrounds.osm"
    extra = sys.argv[2:]
    if not os.path.exists(path):
        fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % BBOX, path)
    if not extra:
        for i, bb in enumerate(CBD_TILES):
            p = "/tmp/adelaide_cbd_%d.osm" % i
            if not os.path.exists(p):
                fetch("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % bb, p)
            extra.append(p)
        for r in RELATIONS:
            p = "/tmp/adelaide_rel_%d.osm" % r
            if not os.path.exists(p):
                fetch("https://api.openstreetmap.org/api/0.6/relation/%d/full" % r, p)
            extra.append(p)
    mapped, ways = load(path, extra)
    st = stadium_ring(ways)
    trees = all_trees(mapped, ways)
    trees += fill_parks(paint(trees, ways), trees, ways, st)
    im = paint(trees, ways)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    paint(trees, ways, NEAR_SIZE, NEAR_SPAN).save(os.path.join(OUT, "surrounds_near.webp"), quality=88, method=6)
    _PX["size"], _PX["ppm"] = SIZE, 1.0
    t = tree_list(trees, st)
    t.tofile(os.path.join(OUT, "trees.bin"))
    b, bc = building_list(ways, st)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    bc.tofile(os.path.join(OUT, "buildings_col.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


if __name__ == "__main__":
    main()
