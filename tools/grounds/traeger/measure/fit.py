"""One smooth closed curve through trace.json's edge readings: the oval's radius from its middle as a Fourier series
in the bearing (orders 0..K), fitted by least squares with outliers (readings more than 0.8 m off once the fit
settles: shade, a tree or a roof edge read as the edge) left out. Prints the residuals in metres by sector and
writes outline.json: the curve's middle, coefficients and 1,440 points (east, north).

    python3 fit.py [K]
"""
import json
import math
import sys

import numpy as np


def design(t, K):
    cols = [np.ones_like(t)]
    for k in range(1, K + 1):
        cols += [np.cos(k * t), np.sin(k * t)]
    return np.stack(cols, 1)


def fit(P, K, c=None, it=12):
    E, N = P[:, 0], P[:, 1]
    if c is None:
        c = np.array([E.mean(), N.mean()])
    keep = np.ones(len(P), bool)
    for i in range(it):
        t = np.arctan2(N - c[1], E - c[0])
        r = np.hypot(E - c[0], N - c[1])
        A = design(t, K)
        co = np.linalg.lstsq(A[keep], r[keep], rcond=None)[0]
        # move the middle so the first harmonic is zero (the curve's own centre), then refit
        c = c + np.array([co[1], co[2]]) if K >= 1 else c
        t = np.arctan2(N - c[1], E - c[0])
        r = np.hypot(E - c[0], N - c[1])
        A = design(t, K)
        co = np.linalg.lstsq(A[keep], r[keep], rcond=None)[0]
        res = r - A @ co
        s = 1.4826 * np.median(np.abs(res[keep]))
        keep = np.abs(res) < max(3 * s, 0.25) if i < 4 else np.abs(res) < 0.8
    return c, co, res, keep


def curve(c, co, K, n=1440):
    t = np.linspace(-math.pi, math.pi, n, endpoint=False)
    r = design(t, K) @ co
    return np.stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)], 1)


if __name__ == "__main__":
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    T = json.load(open("trace.json"))
    P = np.array([[p[0], p[1]] for p in T])
    c, co, res, keep = fit(P, K)
    print("K", K, "centre e %.2f n %.2f" % tuple(c), "readings", len(P), "kept", int(keep.sum()))
    print("residual on kept: rms %.3f m, 95%% %.3f m, max %.3f m" % (np.sqrt((res[keep] ** 2).mean()),
                                                                  np.percentile(np.abs(res[keep]), 95), np.abs(res[keep]).max()))
    t = np.degrees(np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0]))
    for a0 in range(-180, 180, 45):
        s = keep & (t >= a0) & (t < a0 + 45)
        if s.any():
            print("  bearing %4d..%4d (math, from east)  n %4d  mean %+.3f  rms %.3f m" % (a0, a0 + 45, s.sum(), res[s].mean(), np.sqrt((res[s] ** 2).mean())))
    C = curve(c, co, K)
    # its extent along its own long axis
    X = C - c
    w, V = np.linalg.eigh(np.cov(X.T))
    ax = V[:, 1]
    L = X @ ax
    Wd = X @ V[:, 0]
    print("long axis bearing %.2f deg (from north, clockwise)" % (math.degrees(math.atan2(ax[0], ax[1])) % 180),
          "length %.2f m, width %.2f m" % (L.max() - L.min(), Wd.max() - Wd.min()))
    json.dump({"K": K, "centre": c.tolist(), "coef": co.tolist(), "points": C.tolist(),
               "rms": float(np.sqrt((res[keep] ** 2).mean()))}, open("outline.json", "w"))
