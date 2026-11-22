"""York Park's background scene: the land and water past the surroundings map (surrounds.py, the first
1,000 m), out to 25 km. Launceston sits where the North and South Esk meet the Tamar, ringed by hills: Trevallyn
and Cataract Gorge to the west, Windmill Hill, Mowbray and Newstead's slopes, Mount Barrow and the Ben Lomond
foothills east, the Tamar running away north between its bush hills.

    python3 tools/grounds/york_park/backdrop.py <terrarium tile dir> <worldcover.npy> <osm dir>

Heights are the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 13). What covers the land is
ESA WorldCover 2021 (10 m land-cover classes, open data on AWS, read by fetch_cover()): the built-up suburbs,
trees and bush, grass and paddocks, water. Nothing is aerial imagery: each class is painted its Google Earth
colour, mottled.

Within 4 km the suburbs are OpenStreetMap's (fetched in 0.8 km tiles into the OSM dir): the land is painted
at 4 m a pixel (streets by their class, every building's roof, parks, the rivers) over the land cover, and
every mapped building past the surroundings map is stood up on the hillside where it is: houses under a
hipped roof, the rest flat-roofed at their tagged or usual height.

Writes assets/grounds/york_park/york_park_backdrop_part1.glb in model metres (glTF: x east, y up, -z north), the
field's level (5 m above the sea) at 0 and the water a hand under it: the painted land to 4 km, the
vertex-coloured land beyond, and the buildings. The ground rises out of the flat surroundings ring between
1,000 and 1,500 m, so the two meet without a step. Looks only: GroundModels.backdrop() draws it with no
shadows. Map data (c) OpenStreetMap contributors, ODbL; land cover (c) ESA WorldCover project 2021, CC BY 4.0.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "york_park", "york_park_backdrop_part1.glb")
LAT0, LON0 = -41.425896, 147.138976
FIELD_ASL = 5.0
Z = 13
R_IN, R_OUT = 990.0, 25000.0
BLEND = (1000.0, 1500.0)
SEA_Y = -0.12
EARTH_R = 6371000.0

# Google Earth's Launceston in summer, class by class.
WATER = np.array([66, 74, 62], float)       # the Tamar and the Esks run olive-brown
SUBURB = np.array([136, 130, 120], float)   # roofs, roads and gardens together, seen from a few km
TREES = np.array([56, 70, 46], float)       # eucalypt bush on the hills
SHRUB = np.array([96, 100, 70], float)
GRASS = np.array([158, 146, 98], float)     # dry paddocks
CROP = np.array([140, 140, 92], float)
BARE = np.array([150, 138, 116], float)
WET = np.array([92, 104, 76], float)
CLASS = {10: TREES, 20: SHRUB, 30: GRASS, 40: CROP, 50: SUBURB, 60: BARE, 80: WATER, 90: WET, 95: WET, 100: GRASS}
# The cover grid (fetch_cover): 1/12000 degree a cell from lon 146.83, lat -41.19 (north-west corner).
COVER_W, COVER_N, COVER_RES = 146.83, -41.19, 1.0 / 12000


def fetch_cover(path):
    """ESA WorldCover 2021 (v200) round Launceston, from its open bucket, as one uint8 grid."""
    import rasterio
    from rasterio.windows import from_bounds
    L, R_, B, T = COVER_W, 147.45, -41.66, COVER_N
    out = np.zeros((int(round((T - B) / COVER_RES)), int(round((R_ - L) / COVER_RES))), np.uint8)
    for tile in ("S42E144", "S42E147"):
        u = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
             "ESA_WorldCover_10m_2021_v200_%s_Map.tif" % tile)
        with rasterio.open(u) as d:
            lft, rgt = max(L, d.bounds.left), min(R_, d.bounds.right)
            w = from_bounds(lft, B, rgt, T, d.transform).round_offsets().round_lengths()
            a = d.read(1, window=w)
            c0 = int(round((lft - L) / COVER_RES))
            out[:a.shape[0], c0:c0 + a.shape[1]] = a
    np.save(path, out)
    return out


def tile_xy(lat, lon):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n
    return x, y


class Dem:
    def __init__(self, d):
        self.d = d
        lat1, lat2 = LAT0 + R_OUT / 110574, LAT0 - R_OUT / 110574
        dl = R_OUT / (111320 * math.cos(math.radians(LAT0)))
        x0, y0 = tile_xy(lat1, LON0 - dl)
        x1, y1 = tile_xy(lat2, LON0 + dl)
        self.tx0, self.ty0 = int(x0), int(y0)
        nx, ny = int(x1) - self.tx0 + 1, int(y1) - self.ty0 + 1
        self.h = np.zeros((ny * 256, nx * 256), np.float32)
        for i in range(nx):
            for j in range(ny):
                p = os.path.join(d, "%d_%d_%d.png" % (Z, self.tx0 + i, self.ty0 + j))
                if not os.path.exists(p):
                    urllib.request.urlretrieve("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png"
                                               % (Z, self.tx0 + i, self.ty0 + j), p)
                a = np.asarray(Image.open(p).convert("RGB"), np.float32)
                self.h[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

    def at(self, lat, lon):
        x, y = tile_xy(lat, lon)
        fx, fy = (x - self.tx0) * 256 - 0.5, (y - self.ty0) * 256 - 0.5
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        ax, ay = fx - x0, fy - y0
        H = self.h
        x0 = np.clip(x0, 0, H.shape[1] - 2)
        y0 = np.clip(y0, 0, H.shape[0] - 2)
        return (H[y0, x0] * (1 - ax) * (1 - ay) + H[y0, x0 + 1] * ax * (1 - ay)
                + H[y0 + 1, x0] * (1 - ax) * ay + H[y0 + 1, x0 + 1] * ax * ay)


def noise(shape, cells, seed):
    rng = np.random.default_rng(seed)
    g = rng.random(cells).astype(np.float32)
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.BICUBIC),
                      np.float32) / 255


R_MAP = 4000.0          # the painted land and the buildings reach this far
MAP_PX = 2048           # the painted land: 8,192 m a side, 4 m a pixel
MAP_SPAN = 8192.0
NEAR_MAP = 1000.0       # surrounds.py's map covers the first 1,024 m; its buildings stop at 950 m
# Roofs (Google Earth over Invermay, Mowbray and Trevallyn): red and terracotta tile, charcoal, grey and white
# Colorbond, teal; walls: white and cream weatherboard, red and brown brick.
ROOFS = np.array([(150, 72, 58), (164, 92, 70), (82, 84, 88), (140, 142, 140), (196, 196, 192), (76, 110, 108),
                  (120, 66, 54), (104, 108, 112), (66, 68, 72), (170, 172, 170), (118, 120, 122)], float)
WALLS = np.array([(220, 218, 208), (160, 106, 86), (200, 190, 166), (142, 140, 132), (230, 230, 224), (170, 128, 102)], float)
FLAT_ROOF = np.array([(176, 178, 176), (150, 152, 152), (196, 198, 196), (128, 130, 132)], float)
ROAD = (92, 92, 94)
WIDTH = {"motorway": 16, "trunk": 14, "primary": 13, "secondary": 11, "tertiary": 9, "residential": 7,
         "unclassified": 6, "service": 4, "living_street": 5, "motorway_link": 7, "trunk_link": 7,
         "primary_link": 7, "secondary_link": 7, "tertiary_link": 6}


def lin(c):
    """sRGB 0-255 -> linear 0-255: glTF vertex colours are linear (a texture's pixels are sRGB)"""
    c = np.asarray(c, float) / 255.0
    return np.round(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4) * 255.0)


def en(lat, lon):
    return (lon - LON0) * 111320.0 * math.cos(math.radians(LAT0)), (lat - LAT0) * 110574.0


def load_osm(d):
    import glob
    import xml.etree.ElementTree as ET
    ways, seen = [], set()
    for f in sorted(glob.glob(os.path.join(d, "*.osm"))):
        root = ET.parse(f).getroot()
        nodes = {n.get("id"): en(float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
        for w in root.findall("way"):
            if w.get("id") in seen:
                continue
            seen.add(w.get("id"))
            t = {x.get("k"): x.get("v") for x in w.findall("tag")}
            refs = [n.get("ref") for n in w.findall("nd")]
            if not all(r in nodes for r in refs):
                continue
            ways.append((t, [nodes[r] for r in refs]))
    return ways


def height_fn(dem):
    """the backdrop's ground height (y up, field level 0) at plan points east, north (metres)"""
    def f(E, N):
        E, N = np.asarray(E, float), np.asarray(N, float)
        Rg = np.hypot(E, N)
        h = dem.at(LAT0 + N / 110574.0, LON0 + E / (111320.0 * np.cos(np.radians(LAT0))))
        t = np.clip((Rg - BLEND[0]) / (BLEND[1] - BLEND[0]), 0, 1); t = t * t * (3 - 2 * t)
        return np.maximum(h - FIELD_ASL, 0.0) * t - 0.04 * (1 - t) - Rg ** 2 / (2 * EARTH_R), h
    return f


def cover_rgb(cover, lat, lon):
    ci = np.clip(((COVER_N - lat) / COVER_RES).astype(int), 0, cover.shape[0] - 1)
    cj = np.clip(((lon - COVER_W) / COVER_RES).astype(int), 0, cover.shape[1] - 1)
    col = np.zeros(np.shape(lat) + (3,))
    lut = np.zeros((256, 3)); lut[:] = GRASS
    for k, v in CLASS.items():
        lut[k] = v
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            c = cover[np.clip(ci + di * 2, 0, cover.shape[0] - 1), np.clip(cj + dj * 2, 0, cover.shape[1] - 1)]
            col += lut[c] / 9.0
    return col, cover[ci, cj]


def paint_map(cover, ways):
    """The land to R_MAP at 4 m a pixel: land cover underneath, then OpenStreetMap's parks, water, streets and roofs."""
    from PIL import ImageDraw
    k = MAP_SPAN / MAP_PX
    e = (np.arange(MAP_PX) + 0.5) * k - MAP_SPAN / 2
    E, N = np.meshgrid(e, -e)
    col, cls = cover_rgb(cover, LAT0 + N / 110574.0, LON0 + E / (111320.0 * math.cos(math.radians(LAT0))))
    built = cls == 50
    col[built] = (104, 116, 82)                        # gardens, lawns and street trees between the roofs
    col *= (0.9 + 0.2 * noise(col.shape[:2], (256, 256), 8))[..., None]
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    P = lambda pts: [((x + MAP_SPAN / 2) / k, (MAP_SPAN / 2 - y) / k) for x, y in pts]
    for t, p in ways:
        if len(p) < 3 or p[0] != p[-1]:
            continue
        if t.get("leisure") in ("park", "pitch", "golf_course", "recreation_ground") or t.get("landuse") in ("grass", "recreation_ground"):
            d.polygon(P(p), fill=(112, 128, 74) if t.get("leisure") != "pitch" else (100, 124, 68))
        elif t.get("amenity") == "parking":
            d.polygon(P(p), fill=(112, 110, 106))
        elif t.get("landuse") in ("industrial", "commercial", "retail", "railway"):
            d.polygon(P(p), fill=(126, 124, 116))
    for t, p in ways:
        w = WIDTH.get(t.get("highway"))
        if w and len(p) > 1 and t.get("area") != "yes":
            d.line(P(p), fill=ROAD, width=max(1, int(round(w / k))))
    rng = np.random.default_rng(11)
    for t, p in ways:
        if "building" in t and len(p) > 3 and p[0] == p[-1]:
            house = is_house(t, p)
            c = ROOFS[rng.integers(len(ROOFS))] if house else FLAT_ROOF[rng.integers(len(FLAT_ROOF))]
            d.polygon(P(p), fill=tuple(int(v) for v in c))
    return im


def area(p):
    p = np.asarray(p, float); return 0.5 * float(np.sum(p[:-1, 0] * p[1:, 1] - p[1:, 0] * p[:-1, 1]))


def is_house(t, p):
    return ("height" not in t and t.get("building") in ("house", "detached", "semidetached_house", "bungalow", "yes",
            "residential", "terrace") and abs(area(p)) < 400.0)


def bheight(t):
    try:
        return float(t["height"].replace("m", "").strip())
    except (KeyError, ValueError):
        pass
    try:
        return float(t["building:levels"]) * 3.2 + 1.0
    except (KeyError, ValueError):
        pass
    return {"garage": 2.8, "shed": 2.8, "carport": 2.6, "apartments": 12.0, "industrial": 7.0, "warehouse": 8.0,
            "retail": 6.0, "commercial": 8.0, "school": 7.0, "church": 10.0, "roof": 0.0}.get(t.get("building"), 6.0)


def buildings(ways, hfn):
    """Every mapped building from the surroundings map's edge to R_MAP, stood on the hillside: a house is its
    footprint simplified to its rectangle, walls to 3 m and a hipped roof; anything else is its outline
    (simplified to 0.8 m) at its height under a flat roof. Returns vertices, faces and colours."""
    from shapely.geometry import Polygon
    V, F, C = [], [], []
    rng = np.random.default_rng(29)

    def tri(a, b, c, col):
        n = len(V); V.extend([a, b, c]); F.append((n, n + 1, n + 2)); C.extend([col, col, col])

    def quad(a, b, c, d_, col):
        tri(a, b, c, col); tri(a, c, d_, col)
    count = 0
    for t, p in ways:
        if "building" not in t or len(p) < 4 or p[0] != p[-1] or t.get("layer", "0").startswith("-"):
            continue
        cx, cy = np.mean(np.array(p[:-1]), 0)
        r = math.hypot(cx, cy)
        if r < 950.0 or r > R_MAP or (max(abs(cx), abs(cy)) < 1020.0 and r < 1450.0 and False):
            continue
        poly = Polygon(p)
        if not poly.is_valid or poly.area < 12.0:
            continue
        h = bheight(t)
        if h < 2.0:
            continue
        g, _ = hfn([cx], [cy]); g = float(g[0]) - 0.3      # sits into the slope a little
        house = is_house(t, p)
        wall = tuple(WALLS[rng.integers(len(WALLS))] / 255.0)
        if house:
            R = poly.minimum_rotated_rectangle
            q = list(R.exterior.coords)[:4]
            if area(q + q[:1]) < 0:
                q = q[::-1]
            lv = t.get("building:levels")
            eave = g + (3.0 if lv in (None, "1") else float(lv) * 3.0)
            roofc = tuple(ROOFS[rng.integers(len(ROOFS))] / 255.0)
            for i in range(4):
                a, b = q[i], q[(i + 1) % 4]
                quad((a[0], g, -a[1]), (b[0], g, -b[1]), (b[0], eave, -b[1]), (a[0], eave, -a[1]), wall)
            # hipped roof: the ridge along the long side, 30 degree pitch
            A, B, Cq, D = [np.array(x) for x in q]
            L1, L2 = np.linalg.norm(B - A), np.linalg.norm(D - A)
            if L1 < L2:
                A, B, Cq, D = B, Cq, D, A; L1, L2 = L2, L1
            u = (B - A) / L1; half = L2 / 2; rise = half * 0.58
            mid0 = (A + D) / 2 + u * half; mid1 = (B + Cq) / 2 - u * half
            if L1 - 2 * half < 0.1:
                mid0 = mid1 = (A + Cq) / 2
            top = eave + rise
            P3 = lambda x, z: (x[0], z, -x[1])
            quad(P3(A, eave), P3(B, eave), P3(mid1, top), P3(mid0, top), roofc)
            quad(P3(Cq, eave), P3(D, eave), P3(mid0, top), P3(mid1, top), roofc)
            tri(P3(D, eave), P3(A, eave), P3(mid0, top), roofc)
            tri(P3(B, eave), P3(Cq, eave), P3(mid1, top), roofc)
        else:
            s_ = poly.simplify(0.8, preserve_topology=True)
            if s_.geom_type != "Polygon":
                continue
            q = list(s_.exterior.coords)[:-1]
            if area(q + q[:1]) < 0:
                q = q[::-1]
            top = g + h + 0.3
            roofc = tuple(FLAT_ROOF[rng.integers(len(FLAT_ROOF))] / 255.0)
            for i in range(len(q)):
                a, b = q[i], q[(i + 1) % len(q)]
                quad((a[0], g, -a[1]), (b[0], g, -b[1]), (b[0], top, -b[1]), (a[0], top, -a[1]), wall)
            import trimesh
            try:
                v2, f2 = trimesh.creation.triangulate_polygon(s_, engine="earcut")
            except Exception:
                continue
            for f in f2:
                a, b, c = v2[f[0]], v2[f[1]], v2[f[2]]
                tri((a[0], top, -a[1]), (b[0], top, -b[1]), (c[0], top, -c[1]), roofc)
        count += 1
    print("buildings", count, "triangles", len(F))
    return np.array(V), np.array(F), np.array(C)


def far_trees(cover, hfn, cell=30.0):
    """Trees from the surroundings map's edge to R_MAP, where the land cover says tree: one in each `cell` m
    square that is mostly tree cover, a crown 4-7 m across on a short trunk, as a low eight-faced lump
    (a whole suburb's street and garden trees, the bush on Trevallyn and Windmill Hill). Vertices, faces, colours."""
    rng = np.random.default_rng(41)
    xs = np.arange(-R_MAP, R_MAP, cell) + cell / 2
    E, N = np.meshgrid(xs, xs)
    E = E + rng.uniform(-cell * 0.35, cell * 0.35, E.shape); N = N + rng.uniform(-cell * 0.35, cell * 0.35, N.shape)
    R = np.hypot(E, N)
    lat = LAT0 + N / 110574.0; lon = LON0 + E / (111320.0 * math.cos(math.radians(LAT0)))
    ci = np.clip(((COVER_N - lat) / COVER_RES).astype(int), 0, cover.shape[0] - 1)
    cj = np.clip(((lon - COVER_W) / COVER_RES).astype(int), 0, cover.shape[1] - 1)
    tree = np.zeros(E.shape)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            tree += (cover[np.clip(ci + di, 0, cover.shape[0] - 1), np.clip(cj + dj, 0, cover.shape[1] - 1)] == 10)
    ok = (tree >= 5) & (R > 980.0) & (R < R_MAP)
    E, N = E[ok], N[ok]
    g, _ = hfn(E, N)
    V, F, C = [], [], []
    greens = np.array([(56, 72, 44), (66, 82, 50), (48, 62, 40), (74, 88, 56)], float) / 255.0
    for x, z, y0 in zip(E, N, g):
        r = rng.uniform(2.0, 3.6); h0 = y0 + rng.uniform(2.0, 3.5); h1 = h0 + r * rng.uniform(1.3, 1.9)
        hm = 0.5 * (h0 + h1); c = tuple(greens[rng.integers(len(greens))]); a0 = rng.uniform(0, math.pi / 2)
        ring = [(x + r * math.cos(a0 + k * math.pi / 2), hm, -(z + r * math.sin(a0 + k * math.pi / 2))) for k in range(4)]
        top, bot = (x, h1, -z), (x, h0, -z)
        for k in range(4):
            a, b = ring[k], ring[(k + 1) % 4]
            n = len(V); V += [a, b, top]; F.append((n, n + 2, n + 1)); C += [c, c, c]
            n = len(V); V += [a, b, bot]; F.append((n, n + 1, n + 2)); C += [c, c, c]
    print("far trees", len(E))
    return np.array(V), np.array(F), np.array(C)


def main():
    dem = Dem(sys.argv[1] if len(sys.argv) > 1 else "/tmp/yp_dem")
    cpath = sys.argv[2] if len(sys.argv) > 2 else "/tmp/yp_worldcover.npy"
    cover = np.load(cpath) if os.path.exists(cpath) else fetch_cover(cpath)
    ways = load_osm(sys.argv[3] if len(sys.argv) > 3 else "/tmp/yp_osm_far")
    hfn = height_fn(dem)
    import trimesh
    nb = 480                                   # three quarters of a degree round
    rings = [R_IN]
    while rings[-1] < R_OUT:                   # about 12 m apart at 1 km, growing with the range
        rings.append(min(R_OUT, rings[-1] * 1.02 + 6.0))
    rings = sorted(set(rings + [R_MAP]))
    rr = np.array(rings)
    bb = np.radians(np.arange(nb) * 360.0 / nb)
    B, Rg = np.meshgrid(bb, rr)                # rows: ring, cols: bearing
    E, N = Rg * np.sin(B), Rg * np.cos(B)
    lat = LAT0 + N / 110574.0
    lon = LON0 + E / (111320.0 * np.cos(np.radians(LAT0)))
    y, h = hfn(E, N)
    col, cls = cover_rgb(cover, lat, lon)
    sea = (cls == 80) & (h <= 4.0)
    y = np.where(sea, SEA_Y - Rg ** 2 / (2 * EARTH_R), y)
    n2 = noise(h.shape, (160, 720), 4)
    col *= (0.9 + 0.2 * n2)[..., None]
    col = np.where(sea[..., None], WATER[None, None] * (0.94 + 0.06 * n2[..., None]), col)
    V = np.stack([E, y, -N], -1).reshape(-1, 3)
    nc = nb
    k_map = rings.index(R_MAP)

    def faces(i0, i1):
        F = []
        for i in range(i0, i1):
            for j in range(nc):
                a, b = i * nc + j, i * nc + (j + 1) % nc
                c, d = (i + 1) * nc + j, (i + 1) * nc + (j + 1) % nc
                F += [(a, b, c), (b, d, c)]
        return np.array(F)
    scene = trimesh.Scene()
    # the painted land to R_MAP: its own vertices, UVs on the map
    im = paint_map(cover, ways)
    F_in = faces(0, k_map)
    used = np.unique(F_in); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    Vi = V[used]; uv = np.stack([(Vi[:, 0] + MAP_SPAN / 2) / MAP_SPAN, 1.0 - (-Vi[:, 2] + MAP_SPAN / 2) / MAP_SPAN], 1)
    uv[:, 1] = 1.0 - uv[:, 1]
    mat = trimesh.visual.material.PBRMaterial(name="far_land", baseColorTexture=im, roughnessFactor=1.0, metallicFactor=0.0)
    m_in = trimesh.Trimesh(Vi, remap[F_in], visual=trimesh.visual.TextureVisuals(uv=uv, material=mat), process=False)
    scene.add_geometry(m_in, node_name="far_land", geom_name="far_land")
    # the land beyond, vertex-coloured
    F_out = faces(k_map, len(rings) - 1)
    Cv = np.concatenate([lin(np.clip(col, 0, 255).reshape(-1, 3)), np.full((V.shape[0], 1), 255.0)], 1).astype(np.uint8)
    used = np.unique(F_out); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    m_out = trimesh.Trimesh(V[used], remap[F_out], vertex_colors=Cv[used], process=False)
    scene.add_geometry(m_out, node_name="land", geom_name="land")
    Vb, Fb, Cb = buildings(ways, hfn)
    if len(Fb):
        Cb8 = np.concatenate([lin(np.clip(Cb * 255, 0, 255)), np.full((len(Cb), 1), 255.0)], 1).astype(np.uint8)
        m_b = trimesh.Trimesh(Vb, Fb, vertex_colors=Cb8, process=False)
        scene.add_geometry(m_b, node_name="suburbs", geom_name="suburbs")
    Vt, Ft, Ct = far_trees(cover, hfn)
    if len(Ft):
        Ct8 = np.concatenate([lin(np.clip(Ct * 255, 0, 255)), np.full((len(Ct), 1), 255.0)], 1).astype(np.uint8)
        m_t = trimesh.Trimesh(Vt, Ft, vertex_colors=Ct8, process=False)
        scene.add_geometry(m_t, node_name="far_trees", geom_name="far_trees")
    scene.export(OUT)
    im.save(os.environ.get("YP_FAR_PREVIEW", "/tmp/yp_far_map.jpg"), quality=85)
    print("backdrop", OUT, "land faces", len(F_in) + len(F_out), "sea share %.2f" % sea.mean(),
          "highest %.0f m at bearing %.0f" % (h.max(), np.degrees(B.flat[np.argmax(h)])))


if __name__ == "__main__":
    main()
