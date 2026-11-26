"""Fit grade.py's matrix: Sentinel-2's true colour against Google Earth's straight-down mosaic (qa/mosaic.py),
both at 10 m, over open land only (no OpenStreetMap building, road or built-up area within 15 m), so the
roofs that 10 m cells mix in do not pull the fit.

    TRAEGER_CACHE=... python3 qa/grade_fit.py MOSAIC.png      # prints M for grade.py
"""
import os
import sys

import cv2
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import geo  # noqa: E402

R, CELLS = 1300, 260


def main(path):
    s2 = geo.s2_local("TCI", R, CELLS).astype(np.float32)
    m = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB).astype(np.float32)
    v = (m.sum(-1) > 0).astype(np.float32)
    ms = cv2.resize(m, (CELLS, CELLS), interpolation=cv2.INTER_AREA)
    vs = cv2.resize(v, (CELLS, CELLS), interpolation=cv2.INTER_AREA)
    _, ways = geo.osm(R + 100)
    mask = np.zeros((2 * R, 2 * R), np.uint8)
    for _, t, p in ways:
        pts = np.array([(e + R, R - n) for e, n in p], np.int32)
        if "building" in t or t.get("landuse") in ("residential", "commercial", "industrial", "retail"):
            cv2.fillPoly(mask, [pts], 1)
        elif "highway" in t:
            cv2.polylines(mask, [pts], False, 1, 12)
    mk = ndimage.maximum_filter(cv2.resize(mask.astype(np.float32), (CELLS, CELLS), interpolation=cv2.INTER_AREA), 3)
    ok = (vs > 0.99) & (mk == 0)
    x, y = s2[ok], ms[ok]
    # Match the colour distributions (mean and covariance, the Monge-Kantorovich linear map), not a
    # least-squares regression: cells that do not line up exactly would pull a regression to grey.
    mx, my = x.mean(0), y.mean(0)
    Sx, Sy = np.cov(x.T), np.cov(y.T)
    T = _mk(Sx, Sy)
    M = np.c_[T, my - T @ mx]
    print(len(x), "open-land cells; S2 mean", mx.round(1), "GE mean", my.round(1))
    print("M =", np.round(M, 3).tolist())


def _sqrtm(A):
    w, V = np.linalg.eigh(A)
    return V @ np.diag(np.sqrt(np.maximum(w, 1e-9))) @ V.T


def _mk(Sx, Sy):
    a = _sqrtm(Sx)
    ai = np.linalg.inv(a)
    return ai @ _sqrtm(a @ Sy @ a) @ ai


if __name__ == "__main__":
    main(sys.argv[1])
