"""Trace Traeger Park's oval edge (where the irrigated turf meets the dry grass, concrete or the fence) on registered
Google Earth straight-down shots (register.py), in model metres.

For each of 1,440 directions from the oval's middle, along the normal of a first ellipse fitted to the turf mask,
the turf's look (greenness G - (R + B) / 2 less 0.35 of the brightness, smoothed 0.3 m) is read across +-5 m and the edge put where it falls through half way
between the turf's level inside and the ground's level outside, on its steepest drop. Readings with no clear drop
(shade over the edge, a tree, a building over it) are left out. Writes trace.json: [[east, north, shot], ...].

    python3 trace.py SHOT.png [SHOT.png ...]
"""
import json
import math
import sys

import cv2
import numpy as np
from scipy import ndimage

import register


def turf_mask(a):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    hsv = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    t = (G > R + 12) & (G > B + 2) & (hsv[..., 1] > 70)
    t[:95] = False
    t[940:] = False
    t = cv2.morphologyEx(t.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab = cv2.connectedComponents(t)
    k = np.bincount(lab.ravel())[1:].argmax() + 1
    m = (lab == k).astype(np.uint8)
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))


def trace(path, N=1440, chroma=False):
    reg = json.load(open(path[:-4] + ".reg.json"))
    M = np.array(reg["M"])
    mpp = reg["m_per_px"]
    a = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB).astype(np.float32)
    # turf: green and dark; the ground outside (dry grass, lawn, concrete, red earth) paler or less green
    g = a[..., 1] - (a[..., 0] + a[..., 2]) / 2 - 0.35 * a.mean(-1)
    if chroma:
        # in the light towers' shade the turf stays green in hue though dark: its share of green, scaled
        g = 600.0 * (a[..., 1] / np.maximum(a.sum(-1), 1.0) - 0.36)
    g = ndimage.gaussian_filter(g, 0.3 / mpp)
    m = turf_mask(a)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    (cx, cy), (w, h), ang = cv2.fitEllipse(c)
    A, Bx, th = w / 2, h / 2, math.radians(ang)
    out = []
    span = np.arange(-5.0, 5.0, 0.05) / mpp
    for t in np.linspace(0, 2 * math.pi, N, endpoint=False):
        x, y = A * math.cos(t), Bx * math.sin(t)
        p = np.array([cx + x * math.cos(th) - y * math.sin(th), cy + x * math.sin(th) + y * math.cos(th)])
        nx, ny = math.cos(t) / A, math.sin(t) / Bx
        nrm = np.array([nx * math.cos(th) - ny * math.sin(th), nx * math.sin(th) + ny * math.cos(th)])
        nrm /= np.linalg.norm(nrm)
        q = p[None] + span[:, None] * nrm[None]
        if q[:, 1].min() < 100 or q[:, 1].max() > 935 or q[:, 0].min() < 5 or q[:, 0].max() > 1275:
            continue
        if (q[:, 0] < 90).any() and (q[:, 1] > 880).any():      # GE's map inset
            continue
        v = ndimage.map_coordinates(g, [q[:, 1], q[:, 0]], order=1)
        dv = np.gradient(v)
        j = int(np.argmin(dv))                      # steepest fall going out
        if j < 15 or j > len(v) - 15:
            continue
        inside, outside = np.median(v[max(0, j - 40):j - 8]), np.median(v[j + 8:j + 40])
        if inside - outside < 7 or dv[j] > -0.5:   # no clear edge
            continue
        half = (inside + outside) / 2
        k = j
        while k > 0 and v[k] < half:
            k -= 1
        while k < len(v) - 1 and v[k + 1] >= half:
            k += 1
        f = (v[k] - half) / max(v[k] - v[k + 1], 1e-6)
        uv = q[k] + f * (q[k + 1] - q[k])
        out.append((uv, inside - outside))
    uv = np.array([o[0] for o in out])
    en = register.to_model(reg, uv)
    print(path, len(out), "edge readings")
    tag = path.split("/")[-1][:-4] + ("c" if chroma else "")
    return [[float(e), float(n), tag, float(o[1])] for (e, n), o in zip(en, out)]


if __name__ == "__main__":
    pts = []
    for s in sys.argv[1:]:
        pts += trace(s)
        pts += trace(s, chroma=True)
    json.dump(pts, open("trace.json", "w"))
