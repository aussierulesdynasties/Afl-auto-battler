"""York Park's surroundings from OpenStreetMap (the MCG standard's stage 6, docs/MCG_STANDARD.md).

Invermay round the ground: the Inveresk precinct (the University of Tasmania's buildings, the Tramsheds,
the museum and the old railway workshops) to the south and east, Invermay's streets, houses and
showrooms to the north and west, the North Esk river to the south and the Tamar's east bank in the
south-west corner, painted 2 km a side at 1 m a pixel, with every building stood up and the trees listed.
It reuses the MCG's painter (tools/grounds/mcg/surrounds.py) with Launceston's place and colours, as
Bellerive's does. The water is OpenStreetMap's: the North Esk's riverbank multipolygon (relation 8379570,
its rings joined from the member ways) and the Tamar filled from open water up to its coastline lines.

    python3 tools/grounds/york_park/surrounds.py

Fetches the area from the OpenStreetMap API in nine tiles (cached in YP_OSM, default /tmp/yp_osm).
Writes assets/grounds/york_park/surrounds.webp, trees.bin and buildings.bin (the MCG's formats), in
model metres: x east, z south, the model's origin (the OSM pitch's centroid) at 0, 0.
Map data (c) OpenStreetMap contributors, ODbL. Tree positions near the ground: Esri World Imagery.
"""
import json, math
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

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "york_park")
GLB = os.path.join(OUT, "york_park.glb")
# The model's origin: the centroid of the OSM pitch outline, way 88180346 (work/geo.py).
S.LAT0, S.LON0 = -41.425896, 147.138976
S.PITCH_E, S.PITCH_N = 0.0, 0.0
S.MODEL_R = 0.0
# Google Earth's Invermay in summer: dry straw-olive grass on the Inveresk flats, grey-brown house blocks,
# the North Esk a dark olive-brown (it runs muddy and tidal past the ground).
S.BASE = (134, 130, 92)
S.LAWN = (110, 124, 72)
S.PITCH = (98, 118, 68)
S.URBAN = (122, 122, 106)
S.PARKING = (112, 110, 106)
S.ASPHALT = (86, 86, 88)
S.ROOF = (152, 150, 144)
S.WATER = (66, 74, 62)
SAND = (150, 138, 112)      # the river's mud banks at low tide
SHALLOW = (88, 92, 74)
# Open water: a point well out in the Tamar south-west of the North Esk's mouth (m east/north of the origin).
SEA_SEEDS = [(-1000.0, -1000.0)]
TILES = 3   # 3 x 3 OpenStreetMap tiles over 2.2 km
SPAN = 2400.0
# Gardens: Invermay's yards carry a tree every 28 m or so in Google Earth, smaller than the parks'.
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
    return a | (rr <= rmax[bins])


RIVER_REL = 8379570   # the North Esk's riverbank (natural=water, water=river)


def river_rings():
    """The North Esk's water as closed rings of (east, north): the relation's outer ways joined end to end."""
    path = os.path.join(os.environ.get("YP_OSM", "/tmp/yp_osm"), "rel_%d.osm" % RIVER_REL)
    if not os.path.exists(path):
        req = urllib.request.Request("https://api.openstreetmap.org/api/0.6/relation/%d/full" % RIVER_REL,
                                     headers={"User-Agent": "afl-ground-builder/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    nodes = {n.get("id"): S.en(float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
    ways = {w.get("id"): [n.get("ref") for n in w.findall("nd")] for w in root.findall("way")}
    rel = root.find("relation")
    segs = [ways[m.get("ref")] for m in rel.findall("member") if m.get("type") == "way" and m.get("role") == "outer"]
    rings = []
    while segs:
        ring = list(segs.pop(0))
        while ring[0] != ring[-1]:
            for k, sg in enumerate(segs):
                if sg[0] == ring[-1]:
                    ring += sg[1:]
                elif sg[-1] == ring[-1]:
                    ring += sg[::-1][1:]
                else:
                    continue
                segs.pop(k)
                break
            else:
                break
        rings.append([nodes[n] for n in ring])
    return rings


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
    riv = Image.new("L", (S.SIZE, S.SIZE), 0)
    rd = ImageDraw.Draw(riv)
    for ring in river_rings():
        rd.polygon([S.px(*q) for q in ring], fill=255)
    return sea | (np.asarray(riv) > 0)


def garden_trees(im, trees, ways, foot):
    """Trees in Invermay's back yards: on residential land that is clear of every road, roof and path
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


# Trees near the ground from aerial imagery: OpenStreetMap lists few of Invermay's trees (the gums along
# Invermay Road and the North Esk's banks are missing), so within IMG_R the canopy is found in Esri World Imagery
# (zoom 17, about 0.9 m a pixel: green, darker than lawn and rough-textured) and a tree stood on it every
# 7 m or so, its crown as wide as the patch. The tiles are cached in IMG_DIR. Beyond IMG_R the gardens keep
# their random trees.
IMG_R = 700.0
IMG_Z = 17
IMG_DIR = os.environ.get("YP_IMG", "/tmp/yp_img")


def ortho(r=IMG_R + 50.0):
    """Esri World Imagery resampled to model metres, 1 m a pixel, north up, the origin in the middle."""
    os.makedirs(IMG_DIR, exist_ok=True)
    n = 2 ** IMG_Z

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
            p = os.path.join(IMG_DIR, "%d_%d_%d.jpg" % (IMG_Z, i, j))
            if not os.path.exists(p):
                urllib.request.urlretrieve("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
                                           "MapServer/tile/%d/%d/%d" % (IMG_Z, j, i), p)
            M[(j - Y0) * 256:(j - Y0 + 1) * 256, (i - X0) * 256:(i - X0 + 1) * 256] = \
                np.asarray(Image.open(p).convert("RGB"))
    e = np.arange(-r, r) + 0.5
    E, N = np.meshgrid(e, -e)
    x, y = txy(S.LAT0 + N / 110574.0, S.LON0 + E / (111320.0 * math.cos(math.radians(S.LAT0))))
    px = np.clip(((x - X0) * 256).astype(int), 0, M.shape[1] - 1)
    py = np.clip(((y - Y0) * 256).astype(int), 0, M.shape[0] - 1)
    return M[py, px].astype(float), r


def imagery_trees(existing, blocked):
    """(x, z, height, crown radius, shade) rows for the canopy within IMG_R, clear of `existing` (x, z)
    trees by 5 m and of `blocked(x, z)` (the stadium, the sea)."""
    from scipy import ndimage
    a, r = ortho()
    R_, G_, B_ = a[..., 0], a[..., 1], a[..., 2]
    L = (R_ + G_ + B_) / 3
    m = ndimage.uniform_filter(L, 5)
    tex = np.sqrt(np.maximum(ndimage.uniform_filter(L * L, 5) - m * m, 0))
    can = (2 * G_ - R_ - B_ > 13) & (L < 95) & (tex > 9) & (G_ > R_ + 4)
    can = ndimage.binary_closing(ndimage.binary_opening(can), iterations=2)
    lab, n = ndimage.label(can)
    can &= np.isin(lab, 1 + np.nonzero(ndimage.sum(can, lab, range(1, n + 1)) >= 16)[0])
    dist = ndimage.distance_transform_edt(can)
    ys, xs = np.nonzero(can)
    order = np.argsort(-dist[ys, xs], kind="stable")
    rng = np.random.default_rng(23)
    cell = {}
    for x, z in existing:
        cell.setdefault((int(x // 10), int(z // 10)), []).append((x, z, 2.5))
    out = []
    for k in order:
        x, z = xs[k] - r + 0.5, ys[k] - r + 0.5           # image rows run north to south: z is south
        if math.hypot(x, z) > IMG_R or blocked(x, z):
            continue
        rad = float(np.clip(dist[ys[k], xs[k]] * 1.3, 2.8, 7.0))
        cx, cz = int(x // 10), int(z // 10)
        near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cz + j), [])]
        if any(math.hypot(qx - x, qz - z) < max(5.5, 0.85 * (rad + qr)) for qx, qz, qr in near):
            continue
        cell.setdefault((cx, cz), []).append((x, z, rad))
        h = float(np.clip(rad * 1.6 + rng.uniform(1.5, 3.0), 5.5, 16.0))   # crown low on a short trunk, as yard trees are
        out.append((x, z, h, rad, rng.uniform(0.0, 1.0)))
    return np.array(out, "<f4").reshape(-1, 5)


def main():
    paths = sys.argv[1:]
    if not paths:
        for i in range(TILES):
            for j in range(TILES):
                p = os.path.join(os.environ.get("YP_OSM", "/tmp/yp_osm"), "yp_%d%d.osm") % (i, j)
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
        ways += w
    foot = footprint()

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
    # The tiles reach past the 2,048 m map: keep the listed trees on it (the painter reads its mask under them).
    trees = [e for e in trees if all(abs(c) < S.SIZE / 2 - 2 for c in S.model_xz(*e))]
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
        keep = [not foot[int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))]
                for x, z in t[:, :2]]
        t = t[keep]
    def blocked(x, z):
        i, j = int(np.clip(z + S.SIZE / 2, 0, S.SIZE - 1)), int(np.clip(x + S.SIZE / 2, 0, S.SIZE - 1))
        return bool(foot[i, j] or sea[i, j] or math.hypot(x, z) < 105.0)
    img = imagery_trees([tuple(q) for q in t[:, :2]], blocked)
    t = np.concatenate([t.reshape(-1, 5), img]).astype("<f4")
    print("imagery trees", len(img))
    t.astype("<f4").tofile(os.path.join(OUT, "trees.bin"))
    b = building_list(ways, in_foot)
    b.tofile(os.path.join(OUT, "buildings.bin"))
    print("surrounds.webp", im.size, "trees", len(t), "building floats", len(b), "sea px", int(sea.sum()))


def building_list(ways, in_foot):
    """GMHBA's rule: untagged blocks under 400 m2 and the mapped houses are single-storey houses under a
    hipped roof (a negative height); Invermay is the same weatherboard and brick suburb."""
    out = []
    # neighbours.py models these itself (UTAS Inveresk, Invermay Park, the Invermay Road sheds): leave them out.
    modelled = json.load(open(os.path.join(HERE, "neighbours_used.json")))
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        c = np.array(p[:-1]).mean(0)
        if any(abs(c[0] - e) < 1.0 and abs(c[1] - n) < 1.0 for e, n in modelled):
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


if __name__ == "__main__":
    main()
