"""Bellerive Oval's background scene: the land and water past the surroundings map (surrounds.py, the first
1,000 m), out to 19 km. The eastern shore's hills behind the ground (Rosny Hill, Mount Rumney, the Meehan
Range), the Derwent, Hobart's hills across the river and kunanyi / Mount Wellington, 11 km west.

    python3 tools/grounds/bellerive/backdrop.py <terrarium tile dir>

Heights are the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 13, about 14 m a sample here),
fetched into the tile dir if missing. Nothing is aerial imagery: the land is coloured by its height and
slope (sea, the low suburbs, dry grass and bush on the hills, dolerite near kunanyi's summit).

Writes assets/grounds/bellerive/bellerive_backdrop.glb: one vertex-coloured mesh in model metres (glTF:
x east, y up, -z north), the field's level (10 m above the sea) at 0 and the sea a hand under it. The
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
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "bellerive", "bellerive_backdrop.glb")
LAT0, LON0 = -42.8773092, 147.3737365
FIELD_ASL = 10.0
Z = 13
R_IN, R_OUT = 990.0, 19000.0
BLEND = (1000.0, 1500.0)
SEA_Y = -0.12
EARTH_R = 6371000.0

WATER = np.array([46, 92, 108], float)
SUBURB = np.array([124, 124, 104], float)
GRASS = np.array([152, 142, 96], float)
BUSH = np.array([64, 80, 52], float)
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
    dem = Dem(sys.argv[1] if len(sys.argv) > 1 else "/tmp/bellerive_dem")
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
    bush = np.clip((slope - 0.08) * 6 + (h - 140) / 300 + (n1 - 0.5) * 1.2, 0, 1)
    sub = np.clip((90 - h) / 50 + (6000 - Rg) / 6000 + (n1 - 0.5) * 0.6, 0, 1) * (1 - bush)
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
    m.export(OUT)
    print("backdrop", OUT, "verts", len(V), "faces", len(F), "sea share %.2f" % sea.mean(),
          "highest %.0f m at bearing %.0f" % (h.max(), np.degrees(B.flat[np.argmax(h)])))


if __name__ == "__main__":
    main()
