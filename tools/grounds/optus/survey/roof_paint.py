"""The orange paint on the two riverside pavilions' roofs, traced as polygons (Optus rebuild).

Builds a 0.1 m orthophoto at each roof's height from the six calibrated straight-down shots (ortho.py's method,
gtrace.py), keeps the lit pixels inside the roof outline (survey/pavilions.json) whose red over blue is above THR (grey
roof about 0.8, paint about 2), smooths the mask, and writes its outlines,
simplified to 0.15 m, as pavilions.json <side>.roof_paint. Only the outlines are kept, never the imagery.

    OPTUS_WORK=<folder with views.json and ge/> python3 roof_paint.py [preview.png]
"""
import json, math, os, sys
import numpy as np
from matplotlib.path import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gtrace as G

THR = 1.3
SHADE_L = 95.0     # a roof pixel this dark (0-255) is in the stadium's shadow
RES = 0.1


def ortho(S, x0, x1, y0, y1, z):
    xs = np.arange(x0, x1, RES) + RES / 2
    ys = np.arange(y1, y0, -RES) - RES / 2
    X, Y = np.meshgrid(xs, ys)
    acc = []
    for s in S:
        u, v = G.proj(s, X, Y, z)
        ok = (u > 3) & (u < 1276) & (v > 3) & (v < 716)
        im = np.stack([nd.map_coordinates(s["im"][..., c], [v, u], order=1, mode="nearest") for c in range(3)], -1)
        bad = nd.map_coordinates(s["bad"].astype(float), [v, u], order=0, mode="nearest") > 0
        im[~ok | bad] = np.nan
        acc.append(im)
    return X, Y, np.nanmedian(np.array(acc), 0)


def dp(P, tol):
    """Douglas-Peucker on an open polyline."""
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    ab = b - a
    L = np.hypot(*ab) or 1e-9
    d = np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / L
    i = int(np.argmax(d))
    if d[i] > tol:
        return np.vstack([dp(P[:i + 1], tol)[:-1], dp(P[i:], tol)])
    return np.array([a, b])


def main():
    pj = os.path.join(HERE, "pavilions.json")
    D = json.load(open(pj))
    S = G.shots()
    fig = plt.figure()
    for side in ("north", "south"):
        o = np.array(D[side]["outline"])
        x0, y0 = o.min(0) - 2
        x1, y1 = o.max(0) + 2
        X, Y, im = ortho(S, x0, x1, y0, y1, D[side]["roof"])
        inside = Path(o).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
        inside = nd.binary_erosion(inside, iterations=3)          # 0.3 m in from the rim
        ratio = (im[..., 0] + 1) / (im[..., 2] + 1)
        # Part of each roof lies in the stadium's morning shadow, where the paint can't be told from the roof reliably
        # (tried: red over blue 0.12 above the shaded roof's median gave ragged, notched shapes). Only the lit roof is
        # traced; the paint's shaded ends are not in the data.
        lum = im.mean(-1)
        shade = inside & (nd.gaussian_filter(lum, 3) < SHADE_L)
        m = (ratio > THR) & inside & ~shade
        m = nd.binary_opening(m, iterations=3)
        m = nd.binary_closing(m, iterations=4)
        lab, n = nd.label(m)
        keep = [i + 1 for i, c in enumerate(nd.sum(m, lab, range(1, n + 1))) if c * RES * RES > 1.0]
        m = np.isin(lab, keep)
        sm = nd.gaussian_filter(m.astype(float), 3.5)   # the paint has soft, swooping edges
        cs = plt.contour(X, Y, sm, levels=[0.5])
        polys = []
        for path in cs.get_paths():
            for poly in path.to_polygons():
                if len(poly) < 4:
                    continue
                poly = poly[:-1] if np.allclose(poly[0], poly[-1]) else poly
                j = int(np.argmax(np.hypot(*(poly - poly[0]).T)))   # a closed ring: simplify its two halves
                P = np.vstack([dp(poly[:j + 1], 0.15)[:-1], dp(np.vstack([poly[j:], poly[:1]]), 0.15)[:-1]])
                area = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], 1)) - np.dot(P[:, 1], np.roll(P[:, 0], 1)))
                if area > 1.0:
                    polys.append(np.round(P, 2).tolist())
        D[side]["roof_paint"] = polys
        share = m.sum() / max(inside.sum(), 1)
        print(side, "roof in shadow (not traced) %.0f%%;" % (100 * shade.sum() / max(inside.sum(), 1)), len(polys), "paint areas,", round(float(m.sum() * RES * RES), 1), "m2, %.0f%% of the roof" % (100 * share))
        if len(sys.argv) > 1:
            plt.figure(figsize=(6, 8))
            plt.imshow(np.clip(im / 255, 0, 1), extent=[x0, x1, y0, y1])
            for P in polys:
                P = np.array(P + P[:1])
                plt.plot(P[:, 0], P[:, 1], "c-", lw=1)
            plt.plot(*np.vstack([o, o[:1]]).T, "y-", lw=0.6)
            plt.savefig(sys.argv[1].replace(".png", "_%s.png" % side), dpi=110)
    D["roof_paint_note"] = ("Orange paint on each roof, traced by roof_paint.py: pixels of a 0.1 m roof-height orthophoto "
                            "with red over blue above %.1f, outlines simplified to 0.15 m. Only the lit roof is traced: about 40%% of each "
                            "roof lies in the stadium's shadow in the imagery, where the paint can't be told apart. Model frame, metres." % THR)
    json.dump(D, open(pj, "w"), indent=1)


if __name__ == "__main__":
    main()
