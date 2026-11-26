"""Google Earth's calibrated camera and the SCG's nearby buildings, for the round-5 measuring tools
(hover.py, colour_cal.py; SCG rebuild, 2026-11-22).

A view is qa/measure_views.json's (ge_compare.py's format: heading h, tilt t, range d, the look-at point
`at` in metres east, north and up of the field centre). Its shot (<workdir>/ge/<name>.png, ge_shoot.js) is
1280 x 720 with ge_compare.FOV's vertical field of view; the status bar beside it (<name>_cam.png) gives
where Google Earth really put the camera, and the camera here goes there too.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, ".."))
import ge_compare as gc     # noqa: E402

G = gc.GROUNDS["scg"]
CX, CZ = G["fit"][0], G["fit"][1]      # the field centre in model metres (x east, z south)


def cam_parts(v, work):
    """P(x, y, z) -> (pixel x, pixel y) for arrays of model metres (nan behind the camera)."""
    e, n, u = v.get("at", [0, 0, 0])
    h, t, d = math.radians(v["h"]), math.radians(v["t"]), v["d"]
    dirv = np.array((math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)))
    cam = np.array((e, n, u)) - d * dirv
    tgt = np.array((e, n, u), float)
    ro = gc.readouts(os.path.join(work, "ge", v["name"] + "_cam.png"))
    if ro and ro[0][0] is not None:
        lift = ro[0][0] - G["ge_alt"] - cam[2]
        cam[2] += lift
        tgt[2] += lift
    f = (tgt - cam) / np.linalg.norm(tgt - cam)
    up0 = np.array((math.sin(h), math.cos(h), 0.0))
    r = np.cross(f, up0)
    r /= np.linalg.norm(r)
    up = np.cross(r, f)
    th = math.tan(math.radians(gc.FOV) / 2)

    def P(x, y, z):
        q = np.stack(np.broadcast_arrays(x - CX, CZ - z, y), -1) - cam
        zc = q @ f
        zc = np.where(zc > 1, zc, np.nan)
        return 640 + (q @ r) / zc / th * 360, 360 - (q @ up) / zc / th * 360
    return P


def buildings():
    """[(name, closed outline (n+1, 2) in model metres)]: near_buildings.bin's (OpenStreetMap's id, less
    Allianz Stadium's outline) and unmapped.json's ("u" and its Google Earth blob)."""
    raw = np.fromfile(os.path.join(ROOT, "near_buildings.bin"), "<f4")
    i, out = 0, []
    while i < len(raw):
        b, n = int(raw[i]), int(raw[i + 1])
        if b != 1223:
            out.append((str(b), raw[i + 3:i + 3 + 2 * n].reshape(-1, 2)))
        i += 3 + 2 * n
    for e in json.load(open(os.path.join(ROOT, "unmapped.json"))):
        p = np.array(e["footprint"])
        out.append(("u%d" % e["ge_blob"], np.vstack([p, p[:1]])))
    return out
