"""Measure the match's painted boundary line (topdown.gd's picture) against the Google Earth trace.

For every traced point of the line (tools/grounds/boundary/traced/<slug>.json, put in the match's frame by
data/ground_boundaries.json), look along the ray from the middle of the goals in the picture for the white
paint within SEARCH metres and report how far the paint's centre is from the traced point.
  python3 tools/grounds/boundary/check_topdown.py OUTDIR SLUG
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SEARCH = 4.0


def main(out, slug):
    cam = json.load(open(os.path.join(out, slug + "_topdown.json")))
    img = np.asarray(Image.open(os.path.join(out, slug + "_topdown.png")).convert("RGB")).astype(float)
    px, metres = cam["px"], cam["metres"]
    ppm = px / metres
    shape = json.load(open(os.path.join(ROOT, "data", "ground_boundaries.json")))["grounds"][slug]
    tr = json.load(open(os.path.join(HERE, "traced", slug + ".json")))
    mx, mz, a = shape["frame"]
    a = math.radians(a)
    u = np.array([math.cos(a), math.sin(a)])
    v = np.array([-math.sin(a), math.cos(a)])
    pts = np.array(tr["line"], float) - [mx, mz]
    pts = np.stack([pts @ u, pts @ v], 1)
    # Paint: bright and grey (the turf is green, the run-off dark green).
    white = img.min(axis=2)
    offs, missed = [], 0
    for p in pts:
        r = float(np.hypot(*p))
        d = p / r
        best = None
        for s in np.arange(r - SEARCH, r + SEARCH, 0.02):
            q = d * s
            x, y = (q[0] / metres + 0.5) * px, (q[1] / metres + 0.5) * px
            if not (0 <= x < px - 1 and 0 <= y < px - 1):
                continue
            w = white[int(y), int(x)]
            if w > 150:
                best = (best or []) + [s]
        if not best:
            missed += 1
            continue
        offs.append(float(np.mean(best)) - r)
    offs = np.array(offs)
    print("%s: %d traced points, paint found at %d (%d not found within %.0f m; the goal mouths have no curve)" %
          (slug, len(pts), len(offs), missed, SEARCH))
    print("  paint centre minus traced point, along the ray: mean %+.2f m, rms %.2f m, p95 |%.2f| m, max |%.2f| m"
          " (one pixel = %.2f m)" % (offs.mean(), math.sqrt((offs ** 2).mean()), np.percentile(np.abs(offs), 95),
                                    np.abs(offs).max(), 1.0 / ppm))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
