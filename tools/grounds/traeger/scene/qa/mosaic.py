"""Join Google Earth's straight-down views (ge_nadir.js over nadir.json) into one north-up mosaic, 0.5 m a
pixel over +-1,300 m round the oval: each pixel from the view whose centre is nearest. Each view is 1280 x
1000 from 800 m over its point at 0.515 m a pixel, centred on (640, 500); Google Earth's bottom bar and top
popup band are left out. The mosaic is a measuring reference: keep it out of the repo.

    python3 mosaic.py SHOTDIR OUT.png
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MPP, CX, CY = 0.515, 640.0, 500.0
R, K = 1300, 2.0


def main(shots, out_path):
    views = json.load(open(os.path.join(HERE, "nadir.json")))
    S = int(2 * R * K)
    out = np.zeros((S, S, 3), np.uint8)
    best = np.full((S, S), 1e9)
    E = (np.arange(S) + 0.5) / K - R
    EE, NN = np.meshgrid(E, -E)
    for v in views:
        p = os.path.join(shots, v["name"] + ".png")
        if not os.path.exists(p):
            continue
        im = np.asarray(Image.open(p).convert("RGB"))
        px = CX + (EE - v["e"]) / MPP
        py = CY - (NN - v["n"]) / MPP
        ok = (px >= 5) & (px < 1275) & (py >= 95) & (py < 940)
        d = np.hypot(px - CX, py - CY)
        take = ok & (d < best)
        out[take] = im[py[take].astype(int), px[take].astype(int)]
        best[take] = d[take]
    Image.fromarray(out).save(out_path)
    print("mosaic", out_path, "covered %.3f" % (best < 1e9).mean())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
