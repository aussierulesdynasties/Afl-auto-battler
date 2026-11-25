"""Stand outlines against Google Earth, straight down: our roofs (and every other part) projected through the
calibrated Google Earth camera, and on each stretch of our outline the distance along its normal to Google Earth's
strongest edge. Projecting the model (not tracing Google Earth's roofs flat) takes care of lean: a roof 20 m up
and 100 m off the camera's axis sits 4 m further out in the picture than its footprint.

    python3 outline.py GE.png CAM_X CAM_Y CAM_H [SHEET.png]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "manuka", "manuka.glb")
FOV = 25.58
ROOFS = ("roof_grey", "roof_white", "canopy_glass")
LIMIT_MEDIAN, LIMIT_P90 = 0.5, 1.5


def model_tris(names=None):
    import trimesh
    sc = trimesh.load(GLB)
    out = []
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        m = sc.geometry[g]
        mat = getattr(m.visual, "material", None)
        if names is not None and getattr(mat, "name", "") not in names:
            continue
        v = trimesh.transform_points(m.vertices, T)
        P = np.c_[v[:, 0], -v[:, 2], v[:, 1]]       # glTF (x, z, -y) back to (x, y, z)
        out.append(P[m.faces])
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def project(P, cam, W=1280, H=720):
    f = H / 2 / math.tan(math.radians(FOV / 2))
    d = cam[2] - P[..., 2]
    u = W / 2 + f * (P[..., 0] - cam[0]) / d
    v = H / 2 - f * (P[..., 1] - cam[1]) / d
    return np.stack([u, v], -1)


def mask(tris, cam, W=1280, H=720):
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    for t in project(tris, cam, W, H):
        dr.polygon([tuple(p) for p in t], fill=255)
    return np.asarray(im) > 0


def main():
    ge = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    cam = tuple(map(float, sys.argv[2:5]))
    H, W = ge.shape[:2]
    g = nd.gaussian_filter(ge.astype(float).mean(2), 0.8)
    E = np.hypot(nd.sobel(g, 0), nd.sobel(g, 1))
    roof = mask(model_tris(ROOFS), cam, W, H)
    allm = mask(model_tris(), cam, W, H)
    res = 2 * cam[2] * math.tan(math.radians(FOV / 2)) / H   # m/px on the turf's plane
    # our roof outline, with its outward normal from the mask's smoothed gradient
    sm = nd.gaussian_filter(roof.astype(float), 1.5)
    gy, gx = np.gradient(sm)
    edge = roof & ~nd.binary_erosion(roof)
    ii, jj = np.where(edge)
    keep = (ii > 70) & (ii < H - 5) & (jj > 5) & (jj < W - 5)
    ii, jj = ii[keep], jj[keep]
    n = -np.stack([gy[ii, jj], gx[ii, jj]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    ks = np.arange(-14, 14.01, 0.5)
    offs = []
    for (i, j), nn in zip(zip(ii, jj), n):
        q = np.array([i, j])[None] + ks[:, None] * nn[None]
        v = nd.map_coordinates(E, [q[:, 0], q[:, 1]], order=1)
        k = int(np.argmax(v))
        offs.append(ks[k] if v[k] > 0.25 * E.max() * 0.2 else np.nan)
    offs = np.array(offs) * res
    cx, cy = W / 2, H / 2
    brg = (np.degrees(np.arctan2(jj - cx, -(ii - cy))) % 360)
    rep = {"limits": {"median_abs_m": LIMIT_MEDIAN, "p90_abs_m": LIMIT_P90}, "sectors": {}}
    for b0 in range(0, 360, 30):
        s = (brg >= b0) & (brg < b0 + 30) & np.isfinite(offs)
        if s.sum() < 10:
            continue
        a = np.abs(offs[s])
        rep["sectors"][b0] = dict(n=int(s.sum()), median_abs=round(float(np.median(a)), 2), p90_abs=round(float(np.percentile(a, 90)), 2),
                                  mean_signed=round(float(np.mean(offs[s])), 2))
    a = np.abs(offs[np.isfinite(offs)])
    rep["all"] = dict(n=int(len(a)), median_abs=round(float(np.median(a)), 2), p90_abs=round(float(np.percentile(a, 90)), 2))
    rep["pass"] = rep["all"]["median_abs"] <= LIMIT_MEDIAN and rep["all"]["p90_abs"] <= LIMIT_P90
    print(json.dumps(rep, indent=1))
    if len(sys.argv) > 5:
        o = Image.fromarray(ge).convert("RGB"); dr = ImageDraw.Draw(o)
        for (i, j), off, nn in zip(zip(ii, jj), offs, n):
            if not np.isfinite(off):
                continue
            c = (0, 255, 0) if abs(off) < 0.5 else (255, 200, 0) if abs(off) < 1.5 else (255, 0, 255)
            dr.point((j, i), fill=c)
        ao = nd.binary_dilation(allm) & ~allm
        a2 = np.asarray(o).copy(); a2[ao] = (0, 200, 255)
        Image.fromarray(a2).save(sys.argv[5])


if __name__ == "__main__":
    main()
