"""Ours against Google Earth along rays from the field's centre, straight down from the same calibrated camera: on
each bearing, the radial shift (m on the turf's plane) that best lays our edge profile from the fence out to 40 m
past it on Google Earth's (normalised cross-correlation of the edge strength), and how well they then agree.

    python3 rays.py GE.png OURS.png CAM_X CAM_Y CAM_H [SHEET.png]
"""
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

from measure import model_fence

FOV = 25.58
LIMIT_MEDIAN, LIMIT_P90 = 0.5, 1.5


def edge(a):
    g = nd.gaussian_filter(a.astype(float).mean(2), 1.0)
    return np.hypot(nd.sobel(g, 0), nd.sobel(g, 1))


def main():
    ge = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    ours = np.asarray(Image.open(sys.argv[2]).convert("RGB").resize((ge.shape[1], ge.shape[0]), Image.LANCZOS))
    cam = tuple(map(float, sys.argv[3:6]))
    H, W = ge.shape[:2]
    f = H / 2 / math.tan(math.radians(FOV / 2))
    res = cam[2] / f
    E1, E2 = edge(ge), edge(ours)
    rf, C = model_fence()
    step = res / 2
    out = []
    for b in np.arange(0, 360, 2.0):
        a = math.radians(b)
        rs = np.arange(rf(b) - 4, rf(b) + 40, step)
        X, Y = C[0] + rs * math.sin(a), C[1] + rs * math.cos(a)
        u, v = W / 2 + (X - cam[0]) / res, H / 2 - (Y - cam[1]) / res
        if (u < 2).any() or (u > W - 3).any() or (v < 62).any() or (v > H - 3).any():
            continue
        p1 = nd.map_coordinates(E1, [v, u], order=1); p2 = nd.map_coordinates(E2, [v, u], order=1)
        best = None
        for k in range(-24, 25):        # +-12 px of shift
            if k >= 0:
                x1, x2 = p1[k:], p2[:len(p2) - k]
            else:
                x1, x2 = p1[:k], p2[-k:]
            x1 = x1 - x1.mean(); x2 = x2 - x2.mean()
            c = float((x1 * x2).sum() / (np.sqrt((x1 * x1).sum() * (x2 * x2).sum()) + 1e-9))
            if best is None or c > best[0]:
                best = (c, k)
        out.append(dict(bearing=float(b), shift_m=best[1] * step, ncc=best[0]))
    good = [o for o in out if o["ncc"] > 0.35]
    a = np.abs([o["shift_m"] for o in good])
    sectors = {}
    for b0 in range(0, 360, 30):
        s = [abs(o["shift_m"]) for o in good if b0 <= o["bearing"] < b0 + 30]
        sg = [o["shift_m"] for o in good if b0 <= o["bearing"] < b0 + 30]
        if s:
            sectors[b0] = dict(n=len(s), median_abs=round(float(np.median(s)), 2), mean_signed=round(float(np.mean(sg)), 2))
    rep = dict(limits=dict(median_abs_m=LIMIT_MEDIAN, p90_abs_m=LIMIT_P90), bearings=len(out), confident=len(good),
               median_abs=round(float(np.median(a)), 2), p90_abs=round(float(np.percentile(a, 90)), 2), sectors=sectors,
               worst=[(o["bearing"], round(o["shift_m"], 2), round(o["ncc"], 2)) for o in sorted(good, key=lambda o: -abs(o["shift_m"]))[:12]])
    rep["pass"] = rep["median_abs"] <= LIMIT_MEDIAN and rep["p90_abs"] <= LIMIT_P90
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
