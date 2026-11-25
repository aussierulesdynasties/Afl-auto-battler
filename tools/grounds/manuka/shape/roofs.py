"""Trace a roof's outline on the calibrated straight-down Google Earth shot and lay it at the roof's height (the
picture shows a roof h m up as if it stood (H - h)/H nearer the camera's axis, so each pixel is scaled back out by
that much): the white Bradman Stand roof, by colour, as one connected region round a seed point.

    python3 roofs.py GE.png CAM_X CAM_Y CAM_H
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
FOV = 25.58


def to_plan(u, v, cam, h, W=1280, H=720):
    f = H / 2 / math.tan(math.radians(FOV / 2))
    d = cam[2] - h
    return cam[0] + (u - W / 2) * d / f, cam[1] - (v - H / 2) * d / f


def trace_region(ge, seed, pred):
    m = pred(ge.astype(float))
    m = nd.binary_opening(m, iterations=1)
    lab, _ = nd.label(m)
    r = lab == lab[seed[1], seed[0]]
    return nd.binary_fill_holes(nd.binary_closing(r, iterations=2))


def outline(region):
    import shapely.geometry as sg
    from skimage import measure
    cs = measure.find_contours(region.astype(float), 0.5)
    c = max(cs, key=len)
    return sg.Polygon([(p[1], p[0]) for p in c])


def white(a):
    mx, mn = a.max(2), a.min(2)
    return (mn > 196) & (mx - mn < 26) & (a[..., 2] >= a[..., 0] - 4)     # the roof's cool white, not the beige concourse


if __name__ == "__main__":
    ge = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    cam = tuple(map(float, sys.argv[2:5]))
    reg = trace_region(ge, (330, 300), white)
    ys, xs = np.where(reg)
    print("region px", reg.sum(), "bbox", xs.min(), xs.max(), ys.min(), ys.max(), file=sys.stderr)
    poly = outline(reg).simplify(1.0)
    h = json.load(open(os.path.join(HERE, "..", "model", "manuka.json")))["bradman"]["roof_top"]
    P = [to_plan(u, v, cam, h) for u, v in poly.exterior.coords[:-1]]
    print(json.dumps({"bradman_roof": [[round(x, 2), round(y, 2)] for x, y in P], "px_area": int(reg.sum())}))
