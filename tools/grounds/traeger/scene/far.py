"""Traeger Park's far scene: the land from R_IN out to R_OUT (24 km), its real heights and colour.

From the oval a crowd sees the Heavitree Range (the MacDonnell Ranges' front ridge) 2 km to the south with
Heavitree Gap where the Todd River and the Stuart Highway pass through it, the ridges running east and west,
Anzac Hill to the north and the low red hills round the town. Heights are the open Terrarium tiles; the colour
is Sentinel-2 (10 m true colour, October 2025), graded to Google Earth's (grade.py) and drawn as one texture.

    python3 far.py OUT.glb

The mesh is rings round the origin (720 bearings) from R_IN, where the near scene (near.py) ends on the same
ring and heights, out to R_OUT with the rings growing 2 % each, so the near hills are sampled about 11 m
apart and the far ones 300 m. The earth's curve is taken off (45 m down at 24 km). Model metres: x east,
y up, z south, the field's level at 0. Looks only: GroundModels.backdrop() draws it with no shadows.
"""
import math
import sys

import numpy as np
from PIL import Image

import geo
import glb
import grade

R_IN, R_OUT = 1300.0, 24000.0
NB = 720
TEX = 4096
EARTH_R = 6371000.0


def field_asl(dem):
    """The oval's level: the median height within 300 m of the origin."""
    g = np.linspace(-300, 300, 31)
    E, N = np.meshgrid(g, g)
    m = np.hypot(E, N) < 300
    return float(np.median(dem.at(E[m], N[m])))


def rings():
    r = [R_IN]
    while r[-1] < R_OUT:
        r.append(min(R_OUT, r[-1] * 1.02 + 4.0))
    return np.array(r)


def main(out):
    dem = geo.Dem(R_OUT + 500)
    h0 = field_asl(dem)
    rr = rings()
    bb = np.radians(np.arange(NB + 1) * 360.0 / NB)      # the seam's column repeated for the texture
    B, Rg = np.meshgrid(bb, rr)
    E, N = Rg * np.sin(B), Rg * np.cos(B)
    y = dem.at(E, N) - h0 - Rg ** 2 / (2 * EARTH_R)
    P = np.stack([E, y, -N], -1).reshape(-1, 3)
    uv = np.stack([(E + R_OUT) / (2 * R_OUT), (R_OUT - N) / (2 * R_OUT)], -1).reshape(-1, 2)
    nc = NB + 1
    F = []
    for i in range(len(rr) - 1):
        a = i * nc + np.arange(NB)
        F.append(np.stack([a, a + nc, a + 1], -1))
        F.append(np.stack([a + 1, a + nc, a + nc + 1], -1))
    F = np.concatenate(F)
    Nrm = glb.grid_normals(P, F)
    if Nrm[:, 1].mean() < 0:
        F = F[:, ::-1]
        Nrm = -Nrm
    img = geo.s2_local("TCI", R_OUT, TEX)
    img = grade.grade(img)
    w = glb.Glb(frame=geo.model_frame())
    m = w.material("far_land", image=glb.jpeg(Image.fromarray(img), 90))
    col = np.full((len(P), 4), 255, np.uint8)
    w.mesh("far_land", P, Nrm, F, m, uv=uv, col=col)
    w.save(out)
    print("far", out, "verts", len(P), "tris", len(F), "field asl %.1f" % h0, "highest %.0f m" % (y.max()))


if __name__ == "__main__":
    main(sys.argv[1])
