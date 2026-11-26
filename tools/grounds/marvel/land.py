"""Marvel's real land, in the model's own frame (x east, y north of the pitch centre, z up; model z = metres above
sea level - 2.6, the turf at 8 m above sea level standing at z 5.4).

Two jobs:
- `python3 tools/grounds/marvel/land.py export` writes assets/grounds/marvel/terrain.bin (GroundTerrain.gd's format)
  from the shared terrain tool (tools/grounds/terrain, PR #2072: Geoscience Australia's 5 m LiDAR DEM, CC BY 4.0).
  That tool's Marvel grid is centred 15.0 m north and 2.3 m west of our pitch centre, and its datum is the LiDAR's
  7.625 m above sea level at its own centre; the file is resampled onto our centre and referred to Google Earth's turf
  (8 m above sea level), so that the game's `floor_y + height` is model z = sea level - 2.6, the frame every Marvel
  height was measured in.
- `z(x, y)` reads that file back for the build scripts (landmarks.py, surrounds.py, parts2.py), so the streets,
  the rail yard and every building's foot stand on the same land the game's ring does.

Checked against Google Earth on 2026-11-23: five ground picks by NAB and Wurundjeri Way (view c_e) all read 7 m
above sea level; the LiDAR gives 7.1 there.
"""
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
BIN = os.path.join(ROOT, "assets", "grounds", "marvel", "terrain.bin")
FLOOR_Z = 5.4          # the turf in the model (GroundModels.FIT["marvel"][2])
TURF_ASL = 8.0         # Google Earth's turf, 5 spots
LAT0, LON0 = -37.816495302702705, 144.9475565216216   # our pitch centre (the frame of every Google Earth pick)


def export():
    sys.path.insert(0, os.environ.get("TERRAIN_DIR", os.path.join(ROOT, "tools", "grounds", "terrain")))
    import terrain
    T = terrain.load("marvel")
    g = terrain.grounds()["marvel"]
    kx = 111320.0 * math.cos(math.radians(LAT0))
    dx = (LON0 - g["lon"]) * kx          # our centre in the tool's frame
    dy = (LAT0 - g["lat"]) * 110574.0
    shift = T.meta["datum_source_m"] - TURF_ASL
    FH, FS, CH, CS = 1000.0, 5.0, 3000.0, 20.0
    r = np.arange(-FH, FH + FS / 2, FS)
    X, Y = np.meshgrid(r, r)
    fine = T.height(X + dx, Y + dy) + shift
    r = np.arange(-CH, CH + CS / 2, CS)
    X, Y = np.meshgrid(r, r)
    coarse = terrain.source_heights(g, X + dx, Y + dy) - TURF_ASL
    with open(BIN, "wb") as f:
        f.write(np.array([FH, FS, fine.shape[0], CH, CS, coarse.shape[0], 0, 0], np.float32).tobytes())
        for G in (fine, coarse):
            G = np.nan_to_num(G, nan=0.0)
            assert np.abs(G).max() < 327, "land beyond the int16 centimetre range"
            f.write(np.round(G * 100).astype("<i2").tobytes())
    print(BIN, "offset", round(dx, 2), round(dy, 2), "datum shift", round(shift, 3))


_G = None


def _grid():
    global _G
    if _G is None:
        b = open(BIN, "rb").read()
        fh, fs, nf = struct.unpack("<3f", b[:12])
        nf = int(nf)
        _G = (fh, fs, nf, np.frombuffer(b[32:32 + 2 * nf * nf], "<i2").reshape(nf, nf).astype(float) / 100.0)
    return _G


def z(x, y):
    """The land's model z at model (x, y) (scalars or arrays), bilinear on the 5 m grid."""
    fh, fs, n, h = _grid()
    px = np.clip((np.asarray(x, float) + fh) / fs, 0.0, n - 1.001)
    py = np.clip((np.asarray(y, float) + fh) / fs, 0.0, n - 1.001)
    i, j = px.astype(int), py.astype(int)
    fx, fy = px - i, py - j
    v = (h[j, i] * (1 - fx) * (1 - fy) + h[j, i + 1] * fx * (1 - fy) + h[j + 1, i] * (1 - fx) * fy
         + h[j + 1, i + 1] * fx * fy)
    return FLOOR_Z + v


def base(ring):
    """The lowest land under a footprint and its centroid (GroundTerrain.base): a building's foot."""
    p = np.asarray(ring, float)[:, :2]
    return float(min(np.min(z(p[:, 0], p[:, 1])), z(*p.mean(0))))


if __name__ == "__main__" and sys.argv[1:] == ["export"]:
    export()
