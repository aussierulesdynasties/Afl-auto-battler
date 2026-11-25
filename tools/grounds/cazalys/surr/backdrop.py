"""Cazaly's Stadium's background scene: the land and sea past the surroundings map (surrounds.py, the first
1,100 m), out to 55 km. The ranges west of Cairns rise 2 km behind the grandstand (Mount Whitfield, the
Lamb Range, Copperlode Dam's hills); Trinity Inlet's mangroves and the Coral Sea lie east, the airport and
the Barron delta north, the cane fields of the Mulgrave valley south to Walsh's Pyramid (21 km) and
Bartle Frere (50 km).

    python3 tools/grounds/cazalys/surr/backdrop.py <terrarium tile dir> <landuse.npz>

Heights are the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 12, about 37 m a sample here),
fetched into the tile dir if missing; their sea floor is below 0, so the sea needs no coastline. The land's
colour follows OpenStreetMap land cover (landuse.py: rainforest, mangroves, cane, suburbs, industry, the
airport) out to 21 km, then height and slope (rainforest on the ranges, cane on the flats). Colours were
read off Google Earth over Cairns. No aerial imagery is used.

Writes assets/grounds/cazalys/cazalys_backdrop.glb: one vertex-coloured mesh in model metres (glTF:
x east, y up, -z north), the field's level at 0 and the sea a hand under it. The flats round the ground are
laid at the field's level (the elevation tiles carry trees and roofs as bumps there), and the land rises out
of the surroundings map (which it runs under from 1,000 m) between 1,100 and 1,600 m, so the two meet without a step.
Looks only: GroundModels.backdrop() draws it unshaded (its light is baked in) with no shadows.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import math
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "cazalys", "cazalys_backdrop.glb")
LAT0, LON0 = -16.935653, 145.749062
FIELD_ASL = 9.4          # the elevation tiles' height at the field (they read a few metres high on the flats)
Z = 12
R_IN, R_OUT = 1000.0, 55000.0
BLEND = (1100.0, 1600.0)
FLAT = 30.0              # below this height (m above sea) the land is the coastal plain: laid flat
SEA_Y = -0.12
EARTH_R = 6371000.0

# Google Earth over Cairns (2026-11-22 captures): dark rainforest on the ranges, olive mangroves, cane in
# greens to straw, grey-green suburbs (roofs among trees), the sea a muddy green-blue near the shore.
COL = {"sea": (62, 104, 112), "water": (58, 86, 84), "mangrove": (60, 74, 50), "forest": (48, 68, 42),
       "scrub": (104, 112, 72), "farm": (120, 132, 74), "grass": (104, 128, 66), "suburb": (122, 124, 108),
       "industry": (146, 145, 138), "airport": (138, 140, 118), "sand": (196, 186, 156)}


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


def wnoise(E, N, cell, seed):
    """Smooth value noise in 0..1 on a grid of `cell` metres over the whole scene."""
    rng = np.random.default_rng(seed)
    n = int(2 * R_OUT / cell) + 3
    g = rng.random((n, n)).astype(np.float32)
    fx, fy = (E + R_OUT) / cell, (N + R_OUT) / cell
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    ax, ay = fx - x0, fy - y0
    ax, ay = ax * ax * (3 - 2 * ax), ay * ay * (3 - 2 * ay)
    return (g[y0, x0] * (1 - ax) * (1 - ay) + g[y0, x0 + 1] * ax * (1 - ay)
            + g[y0 + 1, x0] * (1 - ax) * ay + g[y0 + 1, x0 + 1] * ax * ay)


def main():
    dem = Dem(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cazalys_dem")
    lu = np.load(sys.argv[2])
    cls, res, half = lu["cls"], float(lu["res"]), float(lu["half"])
    names = [str(x) for x in lu["names"]]
    nb = 720                                   # half a degree round
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
    sea = h <= 0.3
    # The plain: flat at the field's level, easing into the true height above FLAT.
    k = np.clip((h - FLAT) / 40.0, 0, 1)
    y = np.where(sea, SEA_Y, np.maximum(h - FIELD_ASL, 0.0) * k + 0.05 * (1 - k))
    t = np.clip((Rg - BLEND[0]) / (BLEND[1] - BLEND[0]), 0, 1)
    t = t * t * (3 - 2 * t)
    y = np.where(sea, SEA_Y, y * t - 0.3 * (1 - t))   # under the surroundings map where the two overlap
    y -= Rg ** 2 / (2 * EARTH_R)               # the earth's curve: 237 m down at 55 km
    dy_r = np.gradient(h, axis=0) / np.gradient(Rg, axis=0)
    dy_b = np.gradient(h, axis=1) / (Rg * (2 * math.pi / nb))
    slope = np.hypot(dy_r, dy_b)
    n1 = wnoise(E, N, 1500.0, 3)              # in the land's own metres, so nothing streaks along the rings
    n2 = wnoise(E, N, 350.0, 4)
    # OpenStreetMap land cover where mapped (inside 21 km), else the ranges are rainforest and the flats cane.
    ix = np.clip((E / res + cls.shape[1] / 2).astype(int), 0, cls.shape[1] - 1)
    iy = np.clip((cls.shape[0] / 2 - N / res).astype(int), 0, cls.shape[0] - 1)
    inside = (np.abs(E) < half) & (np.abs(N) < half)
    c = np.where(inside, cls[iy, ix], 0)
    lab = np.array(names)[c]
    hill = (slope > 0.10) | (h > 60)
    lab = np.where(lab == "unmapped", np.where(hill, "forest", np.where(n1 > 0.55, "scrub", "farm")), lab)
    col = np.zeros(h.shape + (3,), float)
    for k_, v in COL.items():
        col[lab == k_] = v
    # Cane paddocks: each block its own stage, fresh green to straw.
    straw = np.array([150, 140, 92.0])
    f = (lab == "farm")[..., None] * np.clip((n2 - 0.35) * 1.6, 0, 1)[..., None]
    col = col * (1 - f) + straw * f
    # Rainforest: darker in the gullies (lower) and lighter on the high ridges.
    fo = (lab == "forest")[..., None]
    col = np.where(fo, col * (0.85 + 0.3 * np.clip(h / 900.0, 0, 1))[..., None], col)
    col *= (0.92 + 0.16 * n2)[..., None]
    # Hill shade baked in (the mesh is drawn unshaded, GroundModels "terrain_shaded"): Google Earth's
    # light, high in the north-west, with a soft floor so the far sides of the ranges stay green.
    gx = np.gradient(h, axis=1) / (Rg * (2 * math.pi / nb))     # rise per metre clockwise (bearing)
    gr = np.gradient(h, axis=0) / np.gradient(Rg, axis=0)       # rise per metre outward
    # surface normal in (east, north, up)
    ux, uy = np.sin(B), np.cos(B)              # outward
    tx, ty = np.cos(B), -np.sin(B)             # clockwise
    nx = -(gr * ux + gx * tx); ny = -(gr * uy + gx * ty)
    nn = np.sqrt(nx * nx + ny * ny + 1)
    sun = np.array([-0.45, 0.55, 0.70]); sun /= np.linalg.norm(sun)
    lam = (nx * sun[0] + ny * sun[1] + sun[2]) / nn
    col *= np.clip(0.55 + 0.6 * lam, 0.45, 1.15)[..., None]
    deep = np.clip(-h / 10.0, 0, 1)[..., None]
    wcol = np.array(COL["sea"], float)[None, None] * (1 - 0.25 * deep)
    col = np.where(sea[..., None], wcol, col)
    V = np.stack([E, y, -N], -1).reshape(-1, 3)
    # Alpha 0 on the sea: the painted plain (plain.py, laid on by oval3d_terrain.gdshader) stays off it.
    C = np.concatenate([np.clip(col, 0, 255).reshape(-1, 3), np.where(sea, 0.0, 255.0).reshape(-1, 1)], 1).astype(np.uint8)
    nr, nc = len(rings), nb
    i = np.arange(nr - 1)[:, None]; j = np.arange(nc)[None, :]
    a_, b_ = i * nc + j, i * nc + (j + 1) % nc
    c_, d_ = (i + 1) * nc + j, (i + 1) * nc + (j + 1) % nc
    F = np.concatenate([np.stack([a_, c_, b_], -1).reshape(-1, 3), np.stack([b_, c_, d_], -1).reshape(-1, 3)])
    import trimesh
    m = trimesh.Trimesh(V, F, vertex_colors=C, process=False)
    if m.face_normals[0][1] < 0:
        m.invert()
    trimesh.Scene({"terrain_shaded": m}).export(OUT)
    print("backdrop", OUT, "verts", len(V), "faces", len(F), "sea share %.2f" % sea.mean(),
          "highest %.0f m at bearing %.0f" % (h.max(), np.degrees(B.flat[np.argmax(h)])))


if __name__ == "__main__":
    main()
