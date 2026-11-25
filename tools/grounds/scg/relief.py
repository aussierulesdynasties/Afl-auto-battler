"""The land round the SCG, measured with Google Earth's own heights (SCG rebuild, 2026-11-22).

    python3 tools/grounds/scg/relief.py <workdir>       (after hover.py read)

The SCG's turf is 38 m above the sea in Google Earth; the Fox studios' lot and the Entertainment Quarter to
the east stand 5-11 m higher, and the surrounds were drawn level. hover.py reads Google Earth's height under
the mouse on open ground: a point every 50 m over 1.3 km (on roads, paths, paving and grass, off the canopy,
8 m and more from any building) and 4-6 m outside each nearby building's long walls. This makes the land
from those (<workdir>/hover_ground.json, heights over the turf):

- a reading more than 2.5 m above the median of those within 60 m is dropped (a car, an awning, a tree the
  canopy trace missed: the mouse wasn't on the ground);
- each point of a 257 x 257 grid (8 m apart over the 2,048 m map) is the readings' Gaussian-weighted mean
  (30 m), or, far from any reading, a wider one's (150 m);
- it eases to the turf's height (0) at the stadium's back (the surrounds' inner ring, 100 m from the middle)
  over 40 m, where the model's own concourse meets the land.

Writes assets/grounds/scg/relief.bin (GroundModels.relief_at: side, span, then the heights row by row from
the north-west) and prints the fit: each kept reading against the land at its spot (rms, metres).
relief_at(x, z) here gives the same heights to the tools that place buildings and bridges on it.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "..", "..", "assets", "grounds", "scg", "relief.bin")
N, SPAN, INNER, EASE = 257, 2048.0, 100.0, 40.0


def grid(pts):
    xs = np.linspace(-SPAN / 2, SPAN / 2, N)
    X, Z = np.meshgrid(xs, xs)
    H = np.zeros_like(X)
    W = np.zeros_like(X)
    Hw = np.zeros_like(X)
    Ww = np.zeros_like(X)
    for x, z, h in pts:
        d2 = (X - x) ** 2 + (Z - z) ** 2
        w = np.exp(-d2 / (2 * 30.0 ** 2))
        ww = np.exp(-d2 / (2 * 150.0 ** 2))
        H += w * h
        W += w
        Hw += ww * h
        Ww += ww
    near = H / np.maximum(W, 1e-12)
    far = Hw / np.maximum(Ww, 1e-12)
    t = np.clip(W / 0.3, 0, 1)
    G = near * t + far * (1 - t)
    r = np.hypot(X, Z)
    e = np.clip((r - INNER) / EASE, 0, 1)
    return G * (e * e * (3 - 2 * e))


def main(work):
    p = np.array(json.load(open(os.path.join(work, "hover_ground.json"))), float)
    keep = np.ones(len(p), bool)
    for i, (x, z, h) in enumerate(p):
        m = np.hypot(p[:, 0] - x, p[:, 1] - z) < 60
        if h > np.median(p[m, 2]) + 2.5:
            keep[i] = False
    q = p[keep]
    G = grid(q)
    np.r_[N, SPAN, G.ravel()].astype("<f4").tofile(OUT)
    fit = np.array([relief_at(x, z, G) - h for x, z, h in q])
    print("%d ground readouts, %d kept; land from %.1f to %.1f m over the turf; readings vs land rms %.2f m"
          % (len(p), len(q), G.min(), G.max(), np.sqrt((fit ** 2).mean())))


def relief_at(x, z, G=None):
    if G is None:
        if not os.path.exists(OUT):
            return 0.0
        G = np.fromfile(OUT, "<f4")[2:].reshape(N, N)
    fx = np.clip((x / SPAN + 0.5) * (N - 1), 0, N - 1.001)
    fz = np.clip((z / SPAN + 0.5) * (N - 1), 0, N - 1.001)
    ix, iz = int(fx), int(fz)
    tx, tz = fx - ix, fz - iz
    a, b, c, d = G[iz, ix], G[iz, ix + 1], G[iz + 1, ix], G[iz + 1, ix + 1]
    return float((a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + d * tx) * tz)


if __name__ == "__main__":
    main(sys.argv[1])
