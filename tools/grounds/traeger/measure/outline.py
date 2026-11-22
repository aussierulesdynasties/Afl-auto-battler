"""Traeger Park's outline in the stadium model's own frame, from trace.json (trace.py): the turf's edge as one smooth
curve (fit.py, 6 orders), the boundary line as its exact offset inwards, and the goal lines' centres where the long
axis meets the boundary. The offset is set so the boundary is the published 132 m wide (ABC 2022, data/grounds.json);
its length then comes out on its own and is checked against the published 168 m.

    python3 outline.py        writes outline_model.json (x, z in the model's metres: x east-ish, z south-ish)
"""
import json
import math
import sys

import numpy as np

import fit as Fm

sys.path.insert(0, "../scene")
import geo  # noqa: E402

K = 6
WIDTH = 132.0


def offset(C, d):
    """The closed curve C (N x 2, anticlockwise) moved d inwards along its normals."""
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0)
    n = np.stack([t[:, 1], -t[:, 0]], 1)                 # outward for an anticlockwise curve
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return C - d * n


def main():
    T = json.load(open("trace.json"))
    P = np.array([[p[0], p[1]] for p in T])
    x, y = geo.to_model(P[:, 0], P[:, 1])
    Q = np.stack([x, y], 1)
    c, co, res, keep = Fm.fit(Q, K)
    C = Fm.curve(c, co, K, 2880)
    X = C - C.mean(0)
    w, V = np.linalg.eigh(np.cov(X.T))
    ax = V[:, 1] * np.sign(V[1, 1])                      # the long axis, pointing up the model's y (north end)
    across = np.array([ax[1], -ax[0]])
    lo, hi = 0.0, 20.0
    for _ in range(60):                                  # the offset that makes the boundary WIDTH across
        d = (lo + hi) / 2
        B = offset(C, d)
        wd = np.ptp((B - c) @ across)
        lo, hi = (d, hi) if wd > WIDTH else (lo, d)
    B = offset(C, d)
    s = (B - c) @ ax
    length = np.ptp(s)
    ends = []
    for k in (np.argmax(s), np.argmin(s)):
        ends.append(B[k].tolist())
    out = {"frame": "traeger.glb model metres: [x, z] (z south-ish; the model is turned 25.4 deg to north, ../align.json)",
           "fit": {"orders": K, "readings": int(len(Q)), "kept": int(keep.sum()),
                   "rms_m": float(np.sqrt((res[keep] ** 2).mean())),
                   "p95_m": float(np.percentile(np.abs(res[keep]), 95))},
           "turf_edge": [[float(p[0]), float(-p[1])] for p in C[::4]],
           "turf_edge_size_m": [float(np.ptp((C - c) @ ax)), float(np.ptp((C - c) @ across))],
           "boundary_offset_m": float(d),
           "boundary": [[float(p[0]), float(-p[1])] for p in B[::4]],
           "boundary_size_m": [float(length), WIDTH],
           "published_m": [168.0, 132.0],
           "long_axis_xz": [float(ax[0]), float(-ax[1])],
           "goal_line_centres": [[e[0], -e[1]] for e in ends]}
    json.dump(out, open("outline_model.json", "w"), indent=1)
    print("turf edge %.2f x %.2f m; boundary %.2f m inside: %.2f x %.2f (published 168 x 132); goal lines at %s" % (
        *out["turf_edge_size_m"], d, length, WIDTH, np.round(out["goal_line_centres"], 2).tolist()))
    print("long axis (x, z)", np.round(out["long_axis_xz"], 4), "deg from model -z %.2f" % math.degrees(math.atan2(ax[0], ax[1])))


if __name__ == "__main__":
    main()
