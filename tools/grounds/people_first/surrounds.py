"""People First Stadium's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

The Carrara sports precinct (the indoor sports stadium, the Suns' training ovals), the Nerang River to the
north and east, Nerang-Broadbeach Road, the houses and caravan park, and the trees, painted 2 km a side at
1 m a pixel, with every building stood up and every mapped tree listed. A copy of GMHBA's
(tools/grounds/gmhba/surrounds.py) with Carrara's place, colours and the stadium's own footprint.

    python3 tools/grounds/people_first/surrounds.py [a.osm b.osm ...]

With no files it fetches the area from the OpenStreetMap API in four tiles. Writes
assets/grounds/people_first/surrounds.webp, trees.bin and buildings.bin (same formats as the MCG's), in model
metres: x east, z south, the model's origin (not the field's centre) at 0, 0, as GroundModels lays the map.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcg"))
import surrounds as S  # noqa: E402  (the MCG's painter)

LAT0, LON0 = -28.0062937, 153.3671085

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "people_first")
GLBS = [os.path.join(OUT, "people_first_part%d.glb" % k) for k in (1, 2)]
# The model's origin: Google Earth's straight-down grass edge laid on the model's turf edge (qa/ge_compare.py).
S.LAT0, S.LON0 = LAT0, LON0
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Google Earth's Carrara: green subtropical grass with dry patches, grey car parks, the river a dark green.
S.BASE = (104, 124, 76)
S.LAWN = (96, 128, 70)
S.PITCH = (86, 128, 60)
S.URBAN = (120, 122, 108)
S.PARKING = (100, 100, 98)
S.ASPHALT = (94, 92, 88)
S.ROOF = (156, 154, 150)
S.WATER = (52, 70, 62)
S.WOOD = (60, 86, 48)
_area_colour = S.area_colour


def area_colour(t):
    """The MCG's colours, plus the golf course over the river (RACV Royal Pines) as mown grass."""
    if t.get("leisure") == "golf_course":
        return S.LAWN
    return _area_colour(t)


S.area_colour = area_colour
_fill_parks = S.fill_parks


def fill_parks(im, trees, ways):
    """The MCG's park fill, plus Carrara's bush: Google Earth shows the Nerang River's banks lined with
    gums and paperbarks and the mapped woods closed canopy, where OpenStreetMap lists 62 trees in all.
    Woods get a tree every 70 m2 (6 m apart); grass within 35 m of the river one every 45 m2 (5 m apart), a closed belt."""
    added = _fill_parks(im, trees, ways)
    a = np.asarray(im, int)
    water = np.all(np.abs(a - np.array(S.WATER)) < 6, axis=-1)
    wood = np.all(np.abs(a - np.array(S.WOOD)) < 6, axis=-1)
    grass = (a[..., 1] - a[..., 2] > 30) & (a[..., 1] >= a[..., 0] - 30) & ~wood
    nog = Image.new("L", (S.SIZE, S.SIZE), 0)
    nd = ImageDraw.Draw(nog)
    for t, p in ways:
        if (t.get("leisure") in ("pitch", "golf_course") or t.get("highway")) and len(p) > 1:
            if t.get("highway"):
                nd.line([S.px(*q) for q in p], fill=255, width=12)
            elif len(p) > 2:
                nd.polygon([S.px(*q) for q in p], fill=255)
    free = np.asarray(nog) == 0
    near_water = np.asarray(Image.fromarray((water * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(71))) > 0
    bank = grass & near_water & free
    wood &= free
    rng = np.random.default_rng(31)
    have = [S.model_xz(*e) for e in list(trees) + added]
    cell = {}
    for x, z in have:
        cell.setdefault((int(x // 6), int(z // 6)), []).append((x, z))
    out = []
    for mask, dens, gap in ((wood, 1 / 70.0, 6.0), (bank, 1 / 45.0, 5.0)):
        ys, xs = np.nonzero(mask)
        r = np.hypot(xs - S.SIZE / 2, ys - S.SIZE / 2)
        keep = (r > 150) & (r < 980)
        ys, xs = ys[keep], xs[keep]
        want = int(len(xs) * dens)
        n = 0
        for _ in range(want * 6):
            if n >= want or not len(xs):
                break
            k = rng.integers(len(xs))
            x, z = xs[k] - S.SIZE / 2 + rng.random(), ys[k] - S.SIZE / 2 + rng.random()
            cx, cz = int(x // 6), int(z // 6)
            near = [q for i in (-2, -1, 0, 1, 2) for j in (-2, -1, 0, 1, 2) for q in cell.get((cx + i, cz + j), [])]
            if any((qx - x) ** 2 + (qz - z) ** 2 < gap * gap for qx, qz in near):
                continue
            cell.setdefault((cx, cz), []).append((x, z))
            out.append((x + S.PITCH_E, -z + S.PITCH_N))
            n += 1
    print("bush trees", len(out))
    return added + out


S.fill_parks = fill_parks
TILES = [(LON0 - 0.0115 + i * 0.0115, LAT0 - 0.009 + j * 0.009) for i in (0, 1) for j in (0, 1)]


def fetch(lon, lat, path):
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (lon, lat, lon + 0.0115, lat + 0.009)
    req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def stitch(chains):
    """Join a multipolygon's member ways (lists of points) end to end into closed rings."""
    chains = [list(c) for c in chains if len(c) > 1]
    rings = []
    while chains:
        ring = chains.pop(0)
        grew = True
        while ring[0] != ring[-1] and grew:
            grew = False
            for i, c in enumerate(chains):
                if c[0] == ring[-1]:
                    ring += c[1:]
                elif c[-1] == ring[-1]:
                    ring += c[::-1][1:]
                elif c[-1] == ring[0]:
                    ring = c[:-1] + ring
                elif c[0] == ring[0]:
                    ring = c[::-1][:-1] + ring
                else:
                    continue
                chains.pop(i)
                grew = True
                break
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        rings.append(ring)
    return rings


def relations(paths):
    """Every water, wood and park multipolygon touching the area, whole (the map call only returns the member
    ways inside its box, so the Nerang River came back as open pieces): fetched with relation/<id>/full,
    each outer ring stitched closed and painted like a closed way."""
    import xml.etree.ElementTree as ET
    ids = {}
    for p in paths:
        for r in ET.parse(p).getroot().findall("relation"):
            t = {x.get("k"): x.get("v") for x in r.findall("tag")}
            if t.get("type") == "multipolygon" and S.area_colour(t) is not None:
                ids[r.get("id")] = t
    out = []
    for rid, tags in ids.items():
        path = "/tmp/people_first_rel_%s.osm" % rid
        if not os.path.exists(path):
            url = "https://api.openstreetmap.org/api/0.6/relation/%s/full" % rid
            req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                f.write(r.read())
        root = ET.parse(path).getroot()
        nodes = {n.get("id"): S.en(float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
        wid = {w.get("id"): [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
               for w in root.findall("way")}
        rel = [r for r in root.findall("relation") if r.get("id") == rid][0]
        for role in ("outer", "inner"):
            chains = [wid[m.get("ref")] for m in rel.findall("member")
                      if m.get("type") == "way" and m.get("role") == role and m.get("ref") in wid]
            for ring in stitch(chains):
                # An inner ring (an island) is painted after its water, in the base grass.
                out.append((tags if role == "outer" else {"landuse": "grass"}, ring))
    return out


# The reference satellite is looked at, never committed (docs/MCG_STANDARD.md): it lives in the project files.
SAT = os.environ.get("PF_SAT", "/mnt/project-files/people-first-rebuild/review-imagery/reference/sat.png")
SAT_MPP, SAT_X0, SAT_Y0 = 0.2636169345611428, 1031.4608367085457, 1190.0975657999516  # build/sat.json: the model's origin


def sat_paving():
    """Where the ground round the stadium is sealed: OpenStreetMap maps the car parks but not the asphalt that rings the
    stadium out to 150 m (Google Earth: the whole precinct is dark bitumen between grass islands). Each metre of the
    reference satellite (the model's plan source, 607 m a side) is sorted into bitumen, pale paving or other, the sort
    smoothed over 9 m, and only the class is kept: no photo pixel reaches the map. Returns two masks in map pixels."""
    from PIL import ImageFilter as F
    im = Image.open(SAT).convert("RGB")
    side = int(round(im.size[0] * SAT_MPP))
    a = np.asarray(im.resize((side, side), Image.BOX), float)
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    green = (a[..., 1] > a[..., 0] + 4) & (a[..., 1] > a[..., 2] + 4)
    bitumen = (sat < 0.16) & (mx > 40) & (mx < 135) & ~green
    pale = (sat < 0.14) & (mx >= 135) & (mx < 200) & ~green

    def smooth(m):
        return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(F.MedianFilter(9))) > 127
    bitumen, pale = smooth(bitumen), smooth(pale)
    # Fill the holes under 150 m2 (car roofs, shade, kerb grass) so the bitumen reads as one sealed surface.
    from scipy import ndimage as nd
    for m in (bitumen,):
        lab, n = nd.label(~m)
        sizes = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
        m |= np.isin(lab, 1 + np.nonzero(sizes < 150)[0])
    # map pixel of the satellite's top-left metre
    ox = int(round(-SAT_X0 * SAT_MPP + S.SIZE / 2))
    oz = int(round(-SAT_Y0 * SAT_MPP + S.SIZE / 2))
    B = np.zeros((S.SIZE, S.SIZE), bool)
    Pm = np.zeros((S.SIZE, S.SIZE), bool)
    B[oz:oz + side, ox:ox + side] = bitumen
    Pm[oz:oz + side, ox:ox + side] = pale
    return B, Pm


def sat_green():
    """The satellite's grass, sorted and smoothed as in sat_paving, in map pixels."""
    from PIL import ImageFilter as F
    im = Image.open(SAT).convert("RGB")
    side = int(round(im.size[0] * SAT_MPP))
    a = np.asarray(im.resize((side, side), Image.BOX), float)
    green = (a[..., 1] > a[..., 0] + 4) & (a[..., 1] > a[..., 2] + 4) & (a.max(-1) > 70)
    green = np.asarray(Image.fromarray((green * 255).astype(np.uint8)).filter(F.MedianFilter(9))) > 127
    ox = int(round(-SAT_X0 * SAT_MPP + S.SIZE / 2))
    oz = int(round(-SAT_Y0 * SAT_MPP + S.SIZE / 2))
    G = np.zeros((S.SIZE, S.SIZE), bool)
    G[oz:oz + side, ox:ox + side] = green
    return G


def footprint():
    """The stadium's plan (model x, z) as a 1 m mask in the map's pixels, 3 m wider all round: the model
    draws everything inside, so the map paints it plain paving and no OpenStreetMap building stands there."""
    import trimesh
    vs = []
    for g in GLBS:
        sc = trimesh.load(g)
        vs.append(sc.to_geometry().vertices if hasattr(sc, "to_geometry") else sc.dump(concatenate=True).vertices)
    v = np.vstack(vs)
    v = v[v[:, 1] > 0.5]
    m = np.zeros((S.SIZE, S.SIZE), bool)
    ix = np.clip((v[:, 0] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    iz = np.clip((v[:, 2] + S.SIZE / 2).astype(int), 0, S.SIZE - 1)
    m[iz, ix] = True
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
    # Close the bowl: everything inside the outermost ring of the model is the model's.
    a = np.asarray(im) > 0
    yy, xx = np.mgrid[0:S.SIZE, 0:S.SIZE]
    ang = np.arctan2(yy - S.SIZE / 2, xx - S.SIZE / 2)
    rr = np.hypot(yy - S.SIZE / 2, xx - S.SIZE / 2)
    bins = ((ang + math.pi) / (2 * math.pi) * 720).astype(int) % 720
    rmax = np.zeros(720)
    np.maximum.at(rmax, bins[a], rr[a])
    rmax = np.maximum(rmax, np.roll(rmax, 1))
    rmax = np.maximum(rmax, np.roll(rmax, -1))
    return a | (rr <= rmax[bins])


def main():
    paths = sys.argv[1:]
    if not paths:
        paths = []
        for k, (lon, lat) in enumerate(TILES):
            p = "/tmp/people_first_osm_%d.osm" % k
            if not os.path.exists(p):
                fetch(lon, lat, p)
            paths.append(p)
    trees, ways = [], []
    seen = set()
    for p in paths:
        t, w = S.load(p)
        for e in t:
            if e not in seen:
                seen.add(e)
                trees.append(e)
        ways += [(t, q) for t, q in w if not (t.get("type") == "multipolygon")]
    ways += relations(paths)
    foot = footprint()

    def in_foot(pts, need_all=False):
        hits = [foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                for x, z in (S.model_xz(*q) for q in pts)]
        return all(hits) if need_all else any(hits)

    # The stadium's own OpenStreetMap buildings and pitch go: the model is the stadium.
    ways = [(t, p) for t, p in ways if not (("building" in t or t.get("leisure") in ("stadium", "pitch")) and len(p) > 2 and in_foot(p))]
    trees = [e for e in trees if not in_foot([e])]
    im, trees = S.paint(trees, ways)
    arr = np.asarray(im).copy()
    # The precinct's bitumen and paving, painted over grass only (roads, water and roofs keep the map's own).
    B, Pm = sat_paving()
    g = arr.astype(int)
    grassy = (g[..., 1] > g[..., 2] + 20)
    rng = np.random.default_rng(5)
    for m, c in ((B, S.ASPHALT), (Pm, (150, 148, 142))):
        sel = m & grassy
        arr[sel] = np.clip(np.array(c)[None, :] + rng.normal(0, 3, (sel.sum(), 1)), 0, 255).astype(np.uint8)
    # Under and round the model: bitumen, except the satellite's grass islands (the stands hide the rest).
    G = sat_green()
    arr[foot & ~G] = S.ASPHALT
    arr[foot & G] = S.LAWN
    im = Image.fromarray(arr)
    im.save(os.path.join(OUT, "surrounds.webp"), quality=88, method=6)
    t = S.tree_list(trees)
    t = t[[not in_foot([(x + S.PITCH_E, -z + S.PITCH_N)]) for x, z in t[:, :2]]] if len(t) else t
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b))


def street_houses(ways, in_foot):
    """Houses along the streets of the residential blocks: OpenStreetMap maps 58 buildings round Carrara, where
    Google Earth shows streets of single-storey brick and tile homes and the caravan park's rows. A house every
    17 m each side of every residential street inside a residential area, 11 x 13 m, set 7 m back, hipped roof."""
    res = Image.new("L", (S.SIZE, S.SIZE), 0)
    d = ImageDraw.Draw(res)
    for t, p in ways:
        if t.get("landuse") == "residential" and len(p) > 2:
            d.polygon([S.px(*q) for q in p], fill=255)
    block = Image.new("L", (S.SIZE, S.SIZE), 0)
    bd = ImageDraw.Draw(block)
    for t, p in ways:
        if len(p) < 2:
            continue
        if t.get("highway") in S.WIDTH and t.get("highway") not in ("footway", "path", "cycleway", "steps", "track"):
            bd.line([S.px(*q) for q in p], fill=255, width=int(S.WIDTH.get(t["highway"], 6)) + 2)
        if "building" in t or S.area_colour(t) in (S.WATER, S.PARKING, S.PITCH):
            if len(p) > 2:
                bd.polygon([S.px(*q) for q in p], fill=255)
    res, block = np.asarray(res) > 0, np.asarray(block) > 0
    taken = np.zeros_like(block)
    out = []
    for t, p in ways:
        if t.get("highway") not in ("residential", "living_street", "unclassified", "service") or len(p) < 2:
            continue
        if t.get("service") in ("parking_aisle", "driveway"):
            continue
        pts = [np.array(S.model_xz(*q)) for q in p]
        for a, b in zip(pts, pts[1:]):
            seg = b - a
            L = float(np.hypot(*seg))
            if L < 12:
                continue
            u = seg / L
            nrm = np.array([-u[1], u[0]])
            for k in range(int(L // 17)):
                c0 = a + u * (8.5 + 17 * k)
                for side in (1, -1):
                    c = c0 + nrm * side * (S.WIDTH.get(t["highway"], 6) / 2 + 7 + 6.5)
                    corners = [c + u * dx + nrm * dz for dx, dz in ((-5.5, -6.5), (5.5, -6.5), (5.5, 6.5), (-5.5, 6.5))]
                    ok = True
                    for q in corners + [c]:
                        ix, iz = int(q[0] + S.SIZE / 2), int(q[1] + S.SIZE / 2)
                        if not (0 <= ix < S.SIZE and 0 <= iz < S.SIZE) or not res[iz, ix] or block[iz, ix] or taken[iz, ix]:
                            ok = False
                            break
                    if not ok or math.hypot(*c) > 950 or math.hypot(*c) < 160:
                        continue
                    if in_foot([(c[0] + S.PITCH_E, -c[1] + S.PITCH_N)]):
                        continue
                    ix, iz = int(c[0] + S.SIZE / 2), int(c[1] + S.SIZE / 2)
                    taken[max(0, iz - 7):iz + 8, max(0, ix - 7):ix + 8] = True
                    out.append(4.0)
                    out.append(-3.0)
                    for q in corners:
                        out += [float(q[0]), float(q[1])]
    print("street houses", len(out) // 10)
    return out


def building_list(ways, in_foot):
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
        # The houses round Carrara are single storey under a hipped roof: walls to the eaves, then the roof. A
        # negative height tells GroundModels to put a hipped roof on (untagged blocks under 400 m2 are houses).
        a = abs(S._area(np.array(pts + pts[:1])))
        if "height" not in t and "building:levels" not in t and (
                t.get("building") in ("house", "detached", "semidetached_house", "bungalow", "terrace")
                or (t.get("building") == "yes" and a < 400.0)):
            h = -3.0
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    out += street_houses(ways, in_foot)
    out += ms_buildings(ways, in_foot)
    return np.array(out, "<f4")


# Microsoft's Global ML Building Footprints (ODbL, docs/CREDITS_3D.md) fill in the precinct's sheds and halls that
# OpenStreetMap lacks round Carrara: within 450 m, off the stadium, not on an OpenStreetMap building, not in a
# residential area (street_houses draws those). Height from the footprint's own estimate, at least 3 m.
MS_TILE = "https://minedbuildings.z5.web.core.windows.net/global-buildings/2026-02-03/global-buildings.geojsonl/" \
    "RegionName=Australia/quadkey=311213012/part-00044-4feead82-d499-422b-94cb-c036c212127a.c000.csv.gz"


def ms_buildings(ways, in_foot):
    import gzip
    import json
    path = "/tmp/people_first_msbf.csv.gz"
    if not os.path.exists(path):
        urllib.request.urlretrieve(MS_TILE, path)
    taken = [np.array([S.model_xz(*q) for q in p]) for t, p in ways if "building" in t and len(p) > 3]
    resid = [np.array([S.model_xz(*q) for q in p]) for t, p in ways if t.get("landuse") == "residential" and len(p) > 3]

    def inside(x, z, poly):
        c = False
        for i in range(len(poly)):
            (ax, az), (bx, bz) = poly[i], poly[i - 1]
            if (az > z) != (bz > z) and x < ax + (bx - ax) * (z - az) / (bz - az):
                c = not c
        return c
    out = []
    for line in gzip.open(path, "rt"):
        f = json.loads(line)
        ring = f["geometry"]["coordinates"][0]
        en = [S.en(lat, lon) for lon, lat in ring[:-1]]
        pts = [S.model_xz(*q) for q in en]
        cx, cz = sum(x for x, z in pts) / len(pts), sum(z for x, z in pts) / len(pts)
        if math.hypot(cx, cz) > 450 or in_foot(en):
            continue
        if any(inside(cx, cz, q) for q in taken) or any(inside(cx, cz, q) for q in resid):
            continue
        h = max(3.0, float(f["properties"].get("height", -1) or -1))
        out.append(float(len(pts)))
        out.append(h)
        for x, z in pts:
            out += [x, z]
    return out



if __name__ == "__main__":
    main()
