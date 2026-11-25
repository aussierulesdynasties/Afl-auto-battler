"""Manuka's Canberra past the town (town.py, the first 1.1 km) out to 6.5 km: every building and the trees, standing
on far.py's land. This takes in Kingston, Barton, Parkes, Russell, Fyshwick's edge, Narrabundah, Red Hill, Deakin,
Yarralumla, and across the lake Reid, Braddon, Turner and the city (Civic) skyline.

    python3 tools/grounds/manuka/town/mid.py      # writes assets/grounds/manuka/manuka_backdrop_part3.glb

Buildings: Overture Maps (ODbL: OpenStreetMap's footprints and heights, Microsoft's ML footprints with theirs).
The town's own square (1.1 km each way, town.py) and Parliament House and the Black Mountain Tower (far.py) are left
out. Height from Overture, else its floors, else one storey. Houses and small blocks under a hipped roof over the
footprint's rectangle; everything else flat-roofed, its walls banded storey by storey (glass and spandrel as
separate faces, coloured, not a picture), plant on the bigger roofs.
Roof colour: measured off the aerial photo (Esri World Imagery, zoom 16) inside each footprint; looked at only, the
photo is not kept.
Roads: Overture Maps' road segments (ODbL), each a ribbon of its class's width on the land.\nTrees: the ACT Government's LiDAR mature trees (CC BY 4.0, (c) Australian Capital Territory), each a low crown at
its measured height and spread: every tree to 2.5 km, then the larger ones thinning to a tenth by 6.5 km. Houses to 3.5 km, every
other building to 6.5 km.
"""
import json
import math
import os
import sys
import urllib.parse
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ASSETS, C, CACHE, KX, KY, LAT0, LON0, UA, _get, en, latlon  # noqa: E402
import town as T  # noqa: E402
import far  # noqa: E402

R_TOWN = 1100.0          # town.py's square half-side
R_OUT = 6500.0
CELL = 550.0             # mesh blocks (culling)
TREES_ALL = 2500.0
HOUSES_TO = 3500.0      # houses and sheds past this are hidden by the trees and the land, even from the air at a glance
rng = np.random.default_rng(1913)
OVERTURE = "2026-11-18.0"


# ------------------------------------------------------------------ data
def overture():
    path = os.path.join(CACHE, "overture6500.json")
    if not os.path.exists(path):
        import duckdb
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
            os.environ.pop(k, None)
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
        con.execute("CREATE SECRET (TYPE S3, KEY_ID '', SECRET '', REGION 'us-west-2');")
        r = R_OUT
        q = f"""SELECT id, height, num_floors, class, subtype, names.primary, roof_shape, roof_color, facade_color,
                ST_AsGeoJSON(geometry), sources[1].dataset
                FROM read_parquet('s3://overturemaps-us-west-2/release/{OVERTURE}/theme=buildings/type=building/*',
                                  filename=false, hive_partitioning=1)
                WHERE bbox.xmin > {LON0 - r / KX} AND bbox.xmax < {LON0 + r / KX}
                  AND bbox.ymin > {LAT0 - r / KY} AND bbox.ymax < {LAT0 + r / KY}"""
        out = [dict(id=a, height=b, floors=c, cls=d, sub=e, name=f, roof_shape=g, roof_color=h, facade_color=i,
                    g=json.loads(j), src=k) for a, b, c, d, e, f, g, h, i, j, k in con.execute(q).fetchall()]
        json.dump(out, open(path, "w"))
    return json.load(open(path))


def trees():
    """(x, y, crown height, crown radius) of every ACT LiDAR mature tree within R_OUT."""
    path = os.path.join(CACHE, "trees6500.npy")
    if not os.path.exists(path):
        url = "https://services1.arcgis.com/E5n4f1VY84i0xSjy/ArcGIS/rest/services/ACTGOV_Mature_Trees_2020/FeatureServer/0/query"
        r = R_OUT
        env = "%f,%f,%f,%f" % (LON0 - r / KX, LAT0 - r / KY, LON0 + r / KX, LAT0 + r / KY)
        rows, off = [], 0
        while True:
            q = dict(where="1=1", geometry=env, geometryType="esriGeometryEnvelope", inSR=4326, outSR=4326,
                     spatialRel="esriSpatialRelIntersects", outFields="crownHeight,Shape__Area", returnGeometry="false",
                     returnCentroid="true", f="json", resultOffset=off, resultRecordCount=2000, orderByFields="OBJECTID")
            req = urllib.request.Request(url + "?" + urllib.parse.urlencode(q), headers=UA)
            fs = json.load(urllib.request.urlopen(req, timeout=180)).get("features", [])
            for f in fs:
                c, a = f.get("centroid"), f["attributes"]
                if c and a.get("crownHeight"):
                    x, y = en(c["y"], c["x"])
                    # Shape__Area is in Web Mercator square metres: cos^2(latitude) of it on the ground
                    area = float(a["Shape__Area"]) * math.cos(math.radians(LAT0)) ** 2
                    rows.append((x, y, float(a["crownHeight"]), math.sqrt(area / math.pi)))
            off += len(fs)
            if len(fs) < 2000:
                break
        np.save(path, np.array(rows, np.float32))
    return np.load(path)


class Photo:
    """Esri World Imagery at zoom 16, for measuring roof colours only (nothing is kept)."""

    def __init__(self, z=16, r=R_OUT + 200):
        from PIL import Image
        self.z, n = z, 2 ** z
        self.n = n
        x0, y0 = self.txy(LAT0 + r / KY, LON0 - r / KX)
        x1, y1 = self.txy(LAT0 - r / KY, LON0 + r / KX)
        self.X0, self.Y0 = int(x0), int(y0)
        nx, ny = int(x1) - self.X0 + 1, int(y1) - self.Y0 + 1
        self.M = np.zeros((ny * 256, nx * 256, 3), np.uint8)
        d = os.path.join(CACHE, "img%d" % z)
        for i in range(nx):
            for j in range(ny):
                p = _get("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%d/%d/%d"
                         % (z, self.Y0 + j, self.X0 + i), os.path.join(d, "%d_%d_%d.jpg" % (z, self.X0 + i, self.Y0 + j)))
                self.M[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = np.asarray(Image.open(p).convert("RGB"))

    def txy(self, lat, lon):
        lat = np.asarray(lat, float)
        return ((np.asarray(lon, float) + 180) / 360 * self.n,
                (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * self.n)

    def sample(self, pts):
        pts = np.asarray(pts, float)
        lat, lon = latlon(pts[:, 0], pts[:, 1])
        x, y = self.txy(lat, lon)
        ix = np.clip(((x - self.X0) * 256).astype(int), 0, self.M.shape[1] - 1)
        iy = np.clip(((y - self.Y0) * 256).astype(int), 0, self.M.shape[0] - 1)
        return self.M[iy, ix].astype(float)


def roof_rgb(photo, pg):
    inner = pg.buffer(-1.5)
    if inner.is_empty or inner.area < 6:
        inner = pg
    x0, y0, x1, y1 = inner.bounds
    step = 1.0 if inner.area < 600 else 2.0
    xs, ys = np.meshgrid(np.arange(x0, x1, step), np.arange(y0, y1, step))
    pts = np.c_[xs.ravel(), ys.ravel()]
    from shapely import contains_xy
    pts = pts[contains_xy(inner, pts[:, 0], pts[:, 1])]
    if len(pts) < 3:
        return None
    return np.median(photo.sample(pts), 0)


# ------------------------------------------------------------------ the land (far.py's mesh, so nothing floats)
class FarLand:
    def __init__(self):
        mesh = {}
        far.land(mesh)
        V = mesh["v"]
        self.nb = 540
        self.y = V[:, 2].reshape(-1, self.nb)
        E, N = V[:, 0].reshape(-1, self.nb), V[:, 1].reshape(-1, self.nb)
        self.r = np.hypot(E[:, 0] - C[0], N[:, 0] - C[1])

    def z(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        r = np.hypot(x - C[0], y - C[1])
        b = np.degrees(np.arctan2(x - C[0], y - C[1])) % 360 / (360.0 / self.nb)
        i = np.clip(np.interp(r, self.r, np.arange(len(self.r))), 0, len(self.r) - 1.001)
        i0 = i.astype(int); fi = i - i0
        j0 = b.astype(int) % self.nb; j1 = (j0 + 1) % self.nb; fj = b - np.floor(b)
        Y = self.y
        return ((Y[i0, j0] * (1 - fj) + Y[i0, j1] * fj) * (1 - fi) + (Y[i0 + 1, j0] * (1 - fj) + Y[i0 + 1, j1] * fj) * fi)


# ------------------------------------------------------------------ geometry
GLASS = (62, 76, 88)
GLASS_LIGHT = (104, 122, 134)


def key_of(x, y, mat):
    return ((int(math.floor(x / CELL)) + 60, int(math.floor(y / CELL)) + 60), mat)


def walls(acc, key, ring, base, top, col, bands=None):
    """Plain walls, or storey bands: bands = (floor z, storey, glass fraction, glass colour)."""
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        q = lambda p, z: (p[0], p[1], z)
        f = T.shade(col, 0.86 + 0.14 * abs(math.cos(math.atan2(b[1] - a[1], b[0] - a[0]) - 0.6)))
        if bands is None:
            acc.quad(key, q(a, base), q(b, base), q(b, top), q(a, top), f)
            continue
        z0, sh, gf, gcol = bands
        acc.quad(key, q(a, base), q(b, base), q(b, z0), q(a, z0), f)
        z = z0
        while z + sh <= top - 0.5:
            zg = z + sh * (1 - gf)
            acc.quad(key, q(a, z), q(b, z), q(b, zg), q(a, zg), f)
            acc.quad(key, q(a, zg), q(b, zg), q(b, z + sh), q(a, z + sh), gcol)
            z += sh
        acc.quad(key, q(a, z), q(b, z), q(b, top), q(a, top), f)


def house(acc, pg, floor, base, h_total, wcol, rcol):
    """a house from afar: walls on the footprint's rectangle to the eave, a plain hipped roof (two slopes, two hips)
    with a 0.4 m eave"""
    mr = pg.minimum_rotated_rectangle
    P = np.asarray(mr.exterior.coords)[:4]
    e0, e1 = P[1] - P[0], P[2] - P[1]
    L0, L1 = np.linalg.norm(e0), np.linalg.norm(e1)
    if L0 < 1 or L1 < 1:
        return
    u = e0 / L0 if L0 >= L1 else e1 / L1
    hu, hv = max(L0, L1) / 2, min(L0, L1) / 2
    v = np.array([-u[1], u[0]])
    c = P.mean(0)
    pitch = math.tan(math.radians(22.5))
    eave = floor + max(2.6, h_total - hv * pitch) if h_total else floor + 2.75
    R = lambda a, b: c + u * a + v * b
    rect = [tuple(R(-hu, -hv)), tuple(R(hu, -hv)), tuple(R(hu, hv)), tuple(R(-hu, hv))]
    if area_signed(rect) < 0:
        rect = rect[::-1]
    walls(acc, key_of(c[0], c[1], "wall"), rect, base, eave, wcol)
    o = 0.4; HU, HV = hu + o, hv + o; z = eave - o * pitch; ridge = eave + hv * pitch
    k = max(0.0, HU - HV)
    a1, a2, a3, a4 = [(*R(sa * HU, sb * HV), z) for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    r1, r2 = (*R(-k, 0), ridge), (*R(k, 0), ridge)
    key = key_of(c[0], c[1], "roof")
    s_ = lambda f: T.shade(rcol, f)
    acc.quad(key, a1, a2, r2, r1, s_(0.92))
    acc.quad(key, a3, a4, r1, r2, s_(1.04))
    acc.tri(key, a2, a3, r2, s_(0.98))
    acc.tri(key, a4, a1, r1, s_(0.96))


def area_signed(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def crown(acc, x, y, z, h, r, col):
    """a low crown sharing its six points: a square at two-thirds of the height, the top and a dark point under it"""
    zb = z + h * 0.35; zm = z + h * 0.62; zt = z + h
    a0 = rng.random() * math.pi
    V = [(x + r * math.cos(a0 + k * math.pi / 2), y + r * math.sin(a0 + k * math.pi / 2), zm) for k in range(4)]
    V += [(x, y, zt), (x, y, zb)]
    F = [(k, (k + 1) % 4, 4) for k in range(4)] + [((k + 1) % 4, k, 5) for k in range(4)]
    cols = [col] * 4 + [T.shade(col, 1.1), T.shade(col, 0.6)]
    acc.mesh(key_of(x, y, "leaf"), V, F, cols)


ROAD_W = {"motorway": 14.0, "trunk": 12.0, "primary": 11.0, "secondary": 9.0, "tertiary": 8.0, "unclassified": 7.0,
          "residential": 7.0, "living_street": 6.0, "service": 4.0}
ASPHALT = (88, 90, 92)
R_GROUND = 1060.0        # town.py's painted ground ends here (far.R_IN)


def roads_data():
    path = os.path.join(CACHE, "roads6600.json")
    if not os.path.exists(path):
        import duckdb
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
            os.environ.pop(k, None)
        con = duckdb.connect()
        con.execute("INSTALL spatial; LOAD spatial; INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2';")
        con.execute("CREATE SECRET (TYPE S3, KEY_ID '', SECRET '', REGION 'us-west-2');")
        r = 6600.0
        q = f"""SELECT class, ST_AsGeoJSON(geometry) FROM read_parquet(
                's3://overturemaps-us-west-2/release/{OVERTURE}/theme=transportation/type=segment/*', hive_partitioning=1)
                WHERE subtype='road' AND bbox.xmin > {LON0 - r / KX} AND bbox.xmax < {LON0 + r / KX}
                  AND bbox.ymin > {LAT0 - r / KY} AND bbox.ymax < {LAT0 + r / KY}"""
        json.dump([dict(cls=a, g=json.loads(g)) for a, g in con.execute(q).fetchall()], open(path, "w"))
    return json.load(open(path))


def roads(acc, land):
    """Every road past the town's painted ground as a ribbon of its width on the land, a deck on piers over the
    lake (Commonwealth and Kings Avenue bridges)."""
    n = 0
    for rd in roads_data():
        w = ROAD_W.get(rd["cls"])
        if w is None or rd["g"]["type"] != "LineString":
            continue
        P = np.array([en(la, lo) for lo, la in rd["g"]["coordinates"]])
        # subdivide to 20 m so the ribbon follows the land
        pts = [P[0]]
        for a, b in zip(P[:-1], P[1:]):
            k = max(1, int(math.ceil(np.linalg.norm(b - a) / 20.0)))
            pts += [a + (b - a) * (i / k) for i in range(1, k + 1)]
        P = np.array(pts)
        d = np.hypot(P[:, 0] - C[0], P[:, 1] - C[1])
        if d.max() < R_GROUND or d.min() > R_OUT or (rd["cls"] == "service" and d.min() > HOUSES_TO):
            continue
        z = land.z(P[:, 0], P[:, 1])
        water = z < far.LAKE + 0.4
        z = np.where(water, far.LAKE + 5.0, z + 0.5)
        col = T.shade(ASPHALT, 0.95 + 0.1 * rng.random())
        for i in range(len(P) - 1):
            if d[i] < R_GROUND and d[i + 1] < R_GROUND:
                continue
            a, b = P[i], P[i + 1]
            t = b - a; L = np.linalg.norm(t)
            if L < 0.05:
                continue
            nn = np.array([-t[1], t[0]]) / L * w / 2
            key = key_of(a[0], a[1], "roof")
            acc.quad(key, (*(a - nn), z[i]), (*(a + nn), z[i]), (*(b + nn), z[i + 1]), (*(b - nn), z[i + 1]), col)
            if water[i] and water[i + 1]:
                acc.quad(key, (*(a - nn), z[i] - 1.2), (*(b - nn), z[i + 1] - 1.2), (*(b - nn), z[i + 1]), (*(a - nn), z[i]), (196, 194, 188))
                acc.quad(key, (*(b + nn), z[i + 1] - 1.2), (*(a + nn), z[i] - 1.2), (*(a + nn), z[i]), (*(b + nn), z[i + 1]), (196, 194, 188))
                if i % 2 == 0:      # a pier every 40 m
                    T.box(acc, key, tuple(a), tuple(t / L), 2.0, w * 0.6, far.LAKE - 1.0, z[i] - 1.2, (190, 188, 182))
            n += 1
    return n


# ------------------------------------------------------------------ main
def main():
    from shapely.geometry import Point, Polygon, shape
    land = FarLand()
    photo = Photo()
    acc = T.Acc()
    # Parliament House and the tower: far.py draws them
    skip_polys = []
    import xml.etree.ElementTree as ET
    r_ = ET.parse(os.path.join(CACHE, "parl.osm")).getroot()
    nodes = {n.get("id"): en(float(n.get("lat")), float(n.get("lon"))) for n in r_.iter("node")}
    for w in r_.iter("way"):
        if w.get("id") == "5035605":
            skip_polys.append(Polygon([nodes[n.get("ref")] for n in w.iter("nd")]).buffer(4.0))
    skip_polys.append(Point(*en(-35.27552816, 149.09776749)).buffer(60.0))
    nb = nh = nt = 0
    for o in overture():
        g = o["g"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
        for poly in polys:
            ring = [en(la, lo) for lo, la in poly[0]]
            if len(ring) < 4:
                continue
            pg = Polygon(ring)
            if not pg.is_valid:
                pg = pg.buffer(0)
                if pg.geom_type != "Polygon":
                    continue
            c = pg.centroid
            if max(abs(c.x), abs(c.y)) <= R_TOWN or math.hypot(c.x - C[0], c.y - C[1]) > R_OUT or pg.area < 12:
                continue
            if any(sp.contains(c) for sp in skip_polys):
                continue
            ring = T.simplify(T.ccw_ring([tuple(p) for p in list(pg.exterior.coords)[:-1]]), 0.8)
            if len(ring) < 3:
                continue
            P = np.asarray(ring)
            zg = land.z(P[:, 0], P[:, 1])
            base = float(zg.min()) - 1.0
            floor = float(zg.max()) + 0.2
            h = o["height"]
            fl = o["floors"]
            if not h and fl:
                h = fl * 3.2 + 0.8
            small = pg.area < 40
            is_house = not small and pg.area < 420 and (h is None or h < 10.5) and o["cls"] not in ("commercial", "office", "industrial", "retail", "warehouse", "school", "church")
            if (small or is_house) and math.hypot(c.x - C[0], c.y - C[1]) > HOUSES_TO:
                continue
            rgb = roof_rgb(photo, pg)
            if rgb is None:
                rcol = (118, 84, 70)
            else:
                import colorsys
                hh, ss, vv = colorsys.rgb_to_hsv(*[q / 255 for q in rgb])
                rcol = (126, 80, 64) if (0.2 < hh < 0.5 and ss > 0.12) else T.dehaze(rgb)
            r = rng.random()
            if small:
                top = floor + (h or 2.6)
                walls(acc, key_of(c.x, c.y, "wall"), ring, base, top, (178, 174, 166))
                acc.poly(key_of(c.x, c.y, "roof"), [(x, y, top) for x, y in ring], rcol)
            elif is_house:
                house(acc, pg, floor, base, h, T.pick(T.WALLS_HOUSE, r), rcol)
                nh += 1
            else:
                if not h:
                    h = 7.0
                top = floor + h
                wcol = T.pick(T.WALLS_OFFICE if (o["cls"] or "") not in ("apartments", "residential", "hotel") else T.WALLS_FLATS, r)
                bands = None
                if h >= 9.0:
                    sh = 3.6 if (o["cls"] or "") in ("office", "commercial", "government", "civic") or h > 30 else 3.1
                    gf = 0.62 if h > 25 else 0.42
                    bands = (floor + 0.6, sh, gf, GLASS if r < 0.6 else GLASS_LIGHT)
                walls(acc, key_of(c.x, c.y, "wall"), ring, base, top, wcol, bands)
                acc.poly(key_of(c.x, c.y, "roof"), [(x, y, top) for x, y in ring], rcol)
                if pg.area > 500 and h > 12:
                    T.box(acc, key_of(c.x, c.y, "roof"), (c.x, c.y), (1, 0), min(8.0, math.sqrt(pg.area) * 0.25), 5.0, top, top + 3.0, T.shade(wcol, 0.9))
            nb += 1
    nr = roads(acc, land)
    tr = trees()
    for x, y, h, rr in tr:
        d = math.hypot(x - C[0], y - C[1])
        if max(abs(x), abs(y)) <= R_TOWN or d > R_OUT or h < 3.0:
            continue
        if d > TREES_ALL:
            if h < 9.0 or rng.random() > 1.0 - 0.9 * (d - TREES_ALL) / (R_OUT - TREES_ALL):
                continue
        z = float(land.z(x, y))
        col = T.shade((86, 100, 66) if rng.random() < 0.55 else (104, 112, 82), 0.85 + 0.3 * rng.random())
        crown(acc, x, y, z - 0.3, h, max(1.5, min(rr, 14.0)), col)
        nt += 1
    ntri = sum(len(v[0]) for v in acc.parts.values()) + sum(sum(len(f) for f in v[1]) for v in acc.smooth.values())
    out = os.path.join(ASSETS, "manuka_backdrop_part3.glb")
    T.export(acc, None, out)
    print("road quads", nr, "buildings", nb, "houses", nh, "trees", nt, "triangles", ntri, "->", out, "%.1f MB" % (os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
