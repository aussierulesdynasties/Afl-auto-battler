"""Reading Google Earth's straight-down views of Alice Springs (the mosaic, 0.5 m a pixel over +-1,300 m,
made by qa/mosaic.py from 35 views shot 800 m up): where each gum's canopy is and what colour each roof is.

Every view is a perspective from 800 m, so anything tall leans away from the view's centre by its height /
800 of its distance: a roof 4 m up 300 m off-centre shows 1.5 m further out. Both readings undo that lean.
The mosaic is a measuring reference only; none of its pixels is drawn in the game.
"""
import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

R, K = 1300.0, 2.0
CAM_H = 800.0
HERE = os.path.dirname(os.path.abspath(__file__))


class Mosaic:
    def __init__(self, path):
        self.a = np.asarray(Image.open(path).convert("RGB"), np.float32)
        self.valid = self.a.sum(-1) > 0
        v = json.load(open(os.path.join(HERE, "qa", "nadir.json")))
        self.centres = np.array([(q["e"], q["n"]) for q in v], float)

    def px(self, e, n):
        return (e + R) * K, (R - n) * K

    def _centre(self, e, n):
        d = np.hypot(self.centres[:, 0] - e, self.centres[:, 1] - n)
        return self.centres[int(np.argmin(d))]

    def lean(self, e, n, h):
        c = self._centre(e, n)
        return e + (e - c[0]) * h / CAM_H, n + (n - c[1]) * h / CAM_H

    def roof_colour(self, p, h):
        """The roof's colour: the median of its pixels (shifted by the lean, 1 m in from its edge), leaving
        out solar panels (dark blue) and the deepest shadow."""
        from PIL import ImageDraw
        cx, cy = np.mean(p, 0)
        le, ln = self.lean(cx, cy, h)
        de, dn = le - cx, ln - cy
        xs = [self.px(e + de, n + dn) for e, n in p]
        x0, y0 = np.floor(np.min(xs, 0)).astype(int) - 2
        x1, y1 = np.ceil(np.max(xs, 0)).astype(int) + 2
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, self.a.shape[1]), min(y1, self.a.shape[0])
        if x1 <= x0 or y1 <= y0:
            return (188, 186, 180)
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in xs], fill=255)
        m = ndimage.binary_erosion(np.asarray(m) > 0, iterations=2)
        px = self.a[y0:y1, x0:x1][m & self.valid[y0:y1, x0:x1]]
        if len(px) < 6:
            return (188, 186, 180)
        L = px.mean(1)
        keep = (L > 45) & ~((px[:, 2] > px[:, 0] + 12) & (L < 110))
        if keep.sum() >= 6:
            px = px[keep]
        return tuple(float(c) for c in np.median(px, 0))

    def trees(self, can, blocked, chm=None):
        """(e, n, height, crown radius) for every canopy: olive-green, darker than lawn and rough. A crown is
        stood every 6 m or so over the canopy (can: surface.canopy_mask), as wide as the patch, and moved back by the lean. Its height is
        Meta and WRI's canopy height map's tallest cell under the crown (chm, geo.Chm) where that reads a
        tree (3 m or more), else a gum's usual height for its spread."""
        dist = ndimage.distance_transform_edt(can) / K
        ys, xs = np.nonzero(can)
        order = np.argsort(-dist[ys, xs], kind="stable")
        rng = np.random.default_rng(23)
        cell, out = {}, []
        for k in order:
            e, n = xs[k] / K - R, R - ys[k] / K
            rad = float(np.clip(dist[ys[k], xs[k]] * 1.25, 2.2, 9.0))
            h = float(np.clip(rad * 1.9 + rng.uniform(1.5, 4.0), 6.0, 22.0))
            e0, n0 = e, n
            e, n = _unlean(self, e0, n0, 0.8 * h)
            if chm is not None:
                hc = chm.at(e, n, 0.7 * rad)
                if hc >= 3.0:
                    h = float(np.clip(hc + rng.uniform(-0.5, 0.5), 3.5, 28.0))
                    e, n = _unlean(self, e0, n0, 0.8 * h)
            if blocked(e, n) or math.hypot(e, n) > R - 10:
                continue
            cx, cy = int(e // 8), int(n // 8)
            near = [q for i in (-1, 0, 1) for j in (-1, 0, 1) for q in cell.get((cx + i, cy + j), [])]
            if any(math.hypot(qe - e, qn - n) < max(4.5, 0.8 * (rad + qr)) for qe, qn, qr in near):
                continue
            cell.setdefault((cx, cy), []).append((e, n, rad))
            out.append((e, n, h, rad))
        return out


def _unlean(mo, e, n, h):
    c = mo._centre(e, n)
    f = h / CAM_H
    return (e + f * c[0]) / (1 + f), (n + f * c[1]) / (1 + f)
