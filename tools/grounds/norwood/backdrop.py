"""Norwood Oval's background scene: the land past the surroundings map (surrounds.py, the first 1,000 m),
out to 22 km. The Adelaide Hills east of the ground (the Mount Lofty Ranges' face, Mount Lofty 11 km east),
the plains and suburbs, Gulf St Vincent to the west, and the city's towers 2 to 4 km west.

    python3 tools/grounds/norwood/backdrop.py <terrarium tile dir>

Heights are the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 13), fetched into the tile dir
if missing. The land is coloured by its height and slope (the low suburbs, the hills' dry summer grass and
their eucalypt bush). The towers are skyline.json: every building of 22 m or more in the city from
OpenStreetMap (footprint, height and lowest level; tools osm_skyline.py from the backdrop thread), each a
slab on its own footprint with its roof plant set back, standing on the land.

Writes assets/grounds/norwood/norwood_backdrop.glb: vertex-coloured meshes in model metres (glTF: x east,
y up, -z north), the field's level (50 m above the sea) at 0. The ground rises out of the flat surroundings
ring between 1,000 and 1,500 m, so the two meet without a step. Looks only.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "norwood", "norwood_backdrop.glb")
SKY = os.path.join(HERE, "skyline.json")
LAT0, LON0 = -34.919825, 138.630446
FIELD_ASL = 50.0
Z = 13
R_IN, R_OUT = 990.0, 22000.0
BLEND = (1000.0, 1500.0)
SEA_Y = -0.12
EARTH_R = 6371000.0

# Google Earth's Adelaide in early summer: grey-green suburbs under street trees on the plain, straw and
# olive grass on the hills' open slopes, dark grey-green eucalypt bush in the gullies and on the ridges.
WATER = np.array([52, 98, 116], float)
SUBURB = np.array([128, 126, 112], float)
GRASS = np.array([168, 152, 104], float)
BUSH = np.array([66, 78, 56], float)
ROCK = np.array([130, 126, 114], float)


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


def main():
    dem = Dem(sys.argv[1] if len(sys.argv) > 1 else "/tmp/norwood_dem")
    nb = 480                                   # three quarters of a degree round
    rings = [R_IN]
    while rings[-1] < R_OUT:                   # about 12 m apart at 1 km, growing with the range
        rings.append(min(R_OUT, rings[-1] * 1.02 + 6.0))
    rr = np.array(rings)
    bb = np.radians(np.arange(nb) * 360.0 / nb)
    B, Rg = np.meshgrid(bb, rr)                # rows: ring, cols: bearing
    E, N = Rg * np.sin(B), Rg * np.cos(B)
    lat = LAT0 + N / 110574.0
    lon = LON0 + E / (111320.0 * np.cos(np.radians(LAT0)))
    h = dem.at(lat, lon)
    sea = h <= 0.6
    y = np.where(sea, SEA_Y, np.maximum(h - FIELD_ASL, 0.0))
    t = np.clip((Rg - BLEND[0]) / (BLEND[1] - BLEND[0]), 0, 1)
    t = t * t * (3 - 2 * t)
    y = np.where(sea, SEA_Y, y * t - 0.04 * (1 - t))
    y -= Rg ** 2 / (2 * EARTH_R)               # the earth's curve: 28 m down at 19 km
    # Slope from neighbouring samples (metres up per metre across).
    dy_r = np.gradient(h, axis=0) / np.gradient(Rg, axis=0)
    dy_b = np.gradient(h, axis=1) / (Rg * (2 * math.pi / nb))
    slope = np.hypot(dy_r, dy_b)
    n1 = noise(h.shape, (40, 180), 3)
    n2 = noise(h.shape, (160, 720), 4)
    # Bush on the steep and high ground, dry grass on the gentle hills, suburbs low and near.
    bush = np.clip((slope - 0.12) * 5 + (h - 300) / 400 + (n1 - 0.5) * 1.2, 0, 1)
    # Adelaide's suburbs fill the plain to the foot of the hills (about 150 m above the sea).
    sub = np.clip((170 - h) / 40 - np.clip(slope - 0.06, 0, 1) * 8 + (n1 - 0.5) * 0.4, 0, 1) * (1 - bush)
    col = GRASS[None, None] * (1 - bush[..., None]) + BUSH[None, None] * bush[..., None]
    col = col * (1 - sub[..., None]) + SUBURB[None, None] * sub[..., None]
    rock = np.clip((h - 1000) / 120, 0, 1)[..., None]
    col = col * (1 - rock) + ROCK[None, None] * rock
    col *= (0.9 + 0.2 * n2)[..., None]
    deep = np.clip(-h / 8.0, 0, 1)[..., None]
    wcol = WATER[None, None] * (0.94 + 0.06 * n2[..., None]) * (1 - 0.15 * deep) + np.array([74, 130, 136.0]) * 0.0
    col = np.where(sea[..., None], wcol, col)
    # Mesh: model metres (x east, z south), y up.
    V = np.stack([E, y, -N], -1).reshape(-1, 3)
    C = np.concatenate([np.clip(col, 0, 255).reshape(-1, 3), np.full((V.shape[0], 1), 255.0)], 1).astype(np.uint8)
    nr, nc = len(rings), nb
    F = []
    for i in range(nr - 1):
        for j in range(nc):
            a, b = i * nc + j, i * nc + (j + 1) % nc
            c, d = (i + 1) * nc + j, (i + 1) * nc + (j + 1) % nc
            F += [(a, c, b), (b, c, d)]
    import trimesh
    m = trimesh.Trimesh(V, np.array(F), vertex_colors=C, process=False)
    if m.face_normals[0][1] < 0:
        m.invert()
    sc = trimesh.Scene()
    sc.add_geometry(m, node_name="land", geom_name="land")
    sc.add_geometry(towers(dem), node_name="towers", geom_name="towers")
    sc.export(OUT)
    print("backdrop", OUT, "verts", len(V), "faces", len(F), "sea share %.2f" % sea.mean(),
          "highest %.0f m at bearing %.0f" % (h.max(), np.degrees(B.flat[np.argmax(h)])))


# The city's towers: facades by their OSM colour or material where mapped, else the city's own mix seen from
# the east in Google Earth (blue-grey and green glass, pale concrete, sandstone-coloured precast).
FACADES = {"glass": (92, 112, 128), "concrete": (196, 194, 186), "brick": (150, 96, 76), "stone": (196, 180, 150),
           "metal": (170, 172, 172)}
MIX = [(92, 112, 128), (196, 194, 186), (120, 136, 140), (206, 200, 184), (78, 96, 104), (176, 164, 140)]


def towers(dem):
    """One mesh of every skyline.json building: walls and a flat roof, its roof plant a storey high and set
    back 3 m, standing on the land at its own place (heights above the field's level)."""
    import json
    import trimesh
    from shapely.geometry import Polygon
    V, F, C = [], [], []

    def quad(a, b, c, d, col):
        k = len(V)
        V.extend([a, b, c, d])
        C.extend([col] * 4)
        F.extend([(k, k + 1, k + 2), (k, k + 2, k + 3)])

    def prism(pts, y0, y1, col, roof):
        P = Polygon(pts)
        if not P.is_valid or P.area < 4:
            return
        if not P.exterior.is_ccw:
            pts = pts[::-1]
        n = len(pts)
        for i in range(n):
            (x0, n0), (x1, n1) = pts[i], pts[(i + 1) % n]
            quad((x0, y0, -n0), (x1, y0, -n1), (x1, y1, -n1), (x0, y1, -n0), col)
        tri = trimesh.creation.triangulate_polygon(Polygon(pts), engine="earcut")
        vv, ff = tri
        k = len(V)
        for x, nn in vv:
            V.append((x, y1, -nn))
            C.append(roof)
        F.extend([(k + a, k + c, k + b) for a, b, c in ff])     # upward (north is -z)
    rng = np.random.default_rng(11)
    for b in json.load(open(SKY)):
        pts = [tuple(q) for q in b["p"]]
        if math.hypot(*np.mean(pts, axis=0)) < 1000:
            continue                                            # inside the surroundings map: drawn there
        e, nn = np.mean(pts, axis=0)
        g = float(dem.at(LAT0 + nn / 110574.0, LON0 + e / (111320.0 * math.cos(math.radians(LAT0))))) - FIELD_ASL
        g -= (e * e + nn * nn) / (2 * EARTH_R)
        col = None
        for k, v in FACADES.items():
            if k in (b.get("material") or "") or k in (b.get("colour") or ""):
                col = v
        if col is None:
            col = MIX[int(rng.integers(len(MIX)))]
        col = tuple(int(c * f) for c, f in zip(col, (1, 1, 1))) + (255,)
        roof = (150, 150, 146, 255)
        y0 = g + b.get("min", 0.0) - (0.0 if b.get("min", 0.0) > 0 else 2.0)
        y1 = g + b["h"]
        prism(pts, y0, y1, col, roof)
        P = Polygon(pts).buffer(-3.0)
        if not b.get("part") and P.geom_type == "Polygon" and P.area > 30 and b["h"] > 30:
            prism(list(P.exterior.coords)[:-1], y1, y1 + 3.2, (140, 140, 138, 255), (120, 120, 118, 255))
    m = trimesh.Trimesh(np.array(V, float), np.array(F), vertex_colors=np.array(C, np.uint8), process=False)
    print("towers", len(json.load(open(SKY))), "faces", len(F))
    return m


if __name__ == "__main__":
    main()
