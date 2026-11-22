"""York Park's background scene: the land and water past the surroundings map (surrounds.py, the first
1,000 m), out to 25 km. Launceston sits where the North and South Esk meet the Tamar, ringed by hills: Trevallyn
and Cataract Gorge to the west, Windmill Hill, Mowbray and Newstead's slopes, Mount Barrow and the Ben Lomond
foothills east, the Tamar running away north between its bush hills.

    python3 tools/grounds/york_park/backdrop.py <terrarium tile dir> <worldcover.npy>

Heights are the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 13). What covers the land is
ESA WorldCover 2021 (10 m land-cover classes, open data on AWS, read by fetch_cover()): the built-up suburbs,
trees and bush, grass and paddocks, water. Nothing is aerial imagery: each class is painted its Google Earth
colour, mottled.

Writes assets/grounds/york_park/york_park_backdrop.glb: one vertex-coloured mesh in model metres (glTF:
x east, y up, -z north), the field's level (5 m above the sea) at 0 and the water a hand under it. The
ground rises out of the flat surroundings ring between 1,000 and 1,500 m, so the two meet without a step.
Looks only: GroundModels.backdrop() draws it with no shadows.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "york_park", "york_park_backdrop.glb")
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


def main():
    dem = Dem(sys.argv[1] if len(sys.argv) > 1 else "/tmp/yp_dem")
    cpath = sys.argv[2] if len(sys.argv) > 2 else "/tmp/yp_worldcover.npy"
    cover = np.load(cpath) if os.path.exists(cpath) else fetch_cover(cpath)
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
    ci = np.clip(((COVER_N - lat) / COVER_RES).astype(int), 0, cover.shape[0] - 1)
    cj = np.clip(((lon - COVER_W) / COVER_RES).astype(int), 0, cover.shape[1] - 1)
    cls = cover[ci, cj]
    sea = (cls == 80) & (h <= 4.0)
    y = np.where(sea, SEA_Y, np.maximum(h - FIELD_ASL, 0.0))
    t = np.clip((Rg - BLEND[0]) / (BLEND[1] - BLEND[0]), 0, 1)
    t = t * t * (3 - 2 * t)
    y = np.where(sea, SEA_Y, y * t - 0.04 * (1 - t))
    y -= Rg ** 2 / (2 * EARTH_R)               # the earth's curve: 49 m down at 25 km
    # Each vertex takes the mean colour of the cover round it (a 3 x 3 cell patch, about 25 m), so a
    # suburb's parks and a paddock's tree lines blend in rather than flicker.
    col = np.zeros(h.shape + (3,))
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            c = cover[np.clip(ci + di * 2, 0, cover.shape[0] - 1), np.clip(cj + dj * 2, 0, cover.shape[1] - 1)]
            lut = np.zeros((256, 3)); lut[:] = GRASS
            for k, v in CLASS.items():
                lut[k] = v
            col += lut[c] / 9.0
    n2 = noise(h.shape, (160, 720), 4)
    col *= (0.9 + 0.2 * n2)[..., None]
    wcol = WATER[None, None] * (0.94 + 0.06 * n2[..., None])
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
    m.export(OUT)
    print("backdrop", OUT, "verts", len(V), "faces", len(F), "sea share %.2f" % sea.mean(),
          "highest %.0f m at bearing %.0f" % (h.max(), np.degrees(B.flat[np.argmax(h)])))


if __name__ == "__main__":
    main()
