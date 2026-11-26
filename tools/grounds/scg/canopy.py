"""The tree canopy round the SCG traced from Google Earth (SCG rebuild, 2026-11-22).

OpenStreetMap maps Moore Park's trees but hardly any in the Entertainment Quarter, Disney Studios' lot or
along Driver Avenue, where Google Earth shows big figs and gums between the sheds. This traces the canopy
from a Google Earth view straight down over the ground (900 m above the pitch centre, 23.5 degrees field of
view, 1280 x 720) and writes it as a mask on the surrounds map's grid (2048 px, 1 m a pixel, model 0,0 at
the centre), tools/grounds/scg/canopy_ge.png, which paddington.py plants trees in.

    python3 tools/grounds/scg/canopy.py GOOGLE_EARTH_TOP.png

Canopy is dark, green over red, textured (grass is as green but smooth), in blobs of 60 px or more. The
view is placed on the model by the SCG's grass: its blob spans 247 x 287 px over the boundary's 145 x 168 m
(0.587 m a pixel both ways), centred on the boundary's centre; Tramway Oval then lands within 5 m.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = os.path.dirname(os.path.abspath(__file__))
SIZE = 2048
M_PER_PX = 0.587
PX0, PZ0 = 634.5, 351.5       # the SCG boundary's centre in the view
X0, Z0 = -0.5, 7.0            # ... and in the model (OpenStreetMap's boundary 4000006)


def main(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    v = a.mean(-1)
    sd = np.sqrt(np.maximum(nd.uniform_filter(v * v, 15) - nd.uniform_filter(v, 15) ** 2, 0))
    m = (g >= r + 3) & (g >= b - 6) & (v < 105) & (v > 20) & (sd > 7.5)
    m = nd.binary_opening(m, iterations=1)
    m = nd.binary_closing(m, iterations=3)
    m = nd.binary_fill_holes(m)
    m = nd.binary_opening(m, iterations=3)
    m[:50, 670:1115] = False          # Google Earth's "Dismiss" banner
    lab, n = nd.label(m)
    size = nd.sum(m, lab, range(1, n + 1))
    m = np.isin(lab, 1 + np.flatnonzero(size >= 60))
    # onto the map's grid: each map pixel looks up the view pixel over it
    zz, xx = np.mgrid[0:SIZE, 0:SIZE]
    px = np.round(PX0 + (xx - SIZE / 2 + 0.5 - X0) / M_PER_PX).astype(int)
    pz = np.round(PZ0 + (zz - SIZE / 2 + 0.5 - Z0) / M_PER_PX).astype(int)
    ok = (px >= 0) & (px < m.shape[1]) & (pz >= 0) & (pz < m.shape[0])
    out = np.zeros((SIZE, SIZE), bool)
    out[ok] = m[pz[ok], px[ok]]
    Image.fromarray(out).save(os.path.join(ROOT, "canopy_ge.png"), optimize=True)
    print("canopy: %d m2 traced" % out.sum())


if __name__ == "__main__":
    main(sys.argv[1])
