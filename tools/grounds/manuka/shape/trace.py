"""Trace Manuka's turf edge (the foot of the boundary fence) on the aerial photo, bearing by bearing from C.

    python3 trace.py OUT.json [SHEET.jpg]
"""
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho import ortho  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "town"))
from common import C  # noqa: E402


def grass_mask(im):
    a = im.astype(float)
    g = (a[..., 1] > a[..., 0] + 6) & (a[..., 1] > a[..., 2] - 4) & (a[..., 1] < 200)
    return nd.binary_opening(g, iterations=1)


def ge_topdown(path, rng, cx=None, cy=None, fov=25.58):
    """A straight-down Google Earth shot (ge_shoot.js's 1280 x 720 crop, heading 0, tilt 0) centred on (cx, cy) at
    `rng` m from the turf, as (img, x0, y0, res): 25.58 degrees is the crop's vertical field of view (cb53de5)."""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB"))
    res = 2 * rng * math.tan(math.radians(fov / 2)) / im.shape[0]
    cx = C[0] if cx is None else cx
    cy = C[1] if cy is None else cy
    return im, cx - im.shape[1] / 2 * res, cy + im.shape[0] / 2 * res, res


def trace(step=0.5, rmin=55.0, rmax=110.0, src=None):
    im, x0, y0, res = src if src is not None else ortho()
    g = grass_mask(im)
    # the boundary fence's dark line ends the turf too, where green bank lies outside it (the east hill)
    lum = im.astype(float).mean(2)
    i0, j0 = int((y0 - C[1]) / res), int((C[0] - x0) / res)
    turf_lum = np.median(lum[max(0, i0 - 200):i0 + 200, max(0, j0 - 200):j0 + 200][g[max(0, i0 - 200):i0 + 200, max(0, j0 - 200):j0 + 200]])
    dark = lum < 0.62 * turf_lum
    g = g & ~nd.binary_dilation(dark, iterations=1)
    g = g.astype(float)
    # the turf is one connected region round C: keep it, so lawns outside the fence never count
    lab, n = nd.label(g > 0.5)
    keep = lab == lab[i0, j0]
    keep = nd.binary_fill_holes(nd.binary_closing(keep, iterations=1))
    out = []
    rs = np.arange(rmin, rmax, res / 2)
    for b in np.arange(0, 360, step):
        a = math.radians(b)
        X, Y = C[0] + rs * math.sin(a), C[1] + rs * math.cos(a)
        v = nd.map_coordinates(keep.astype(float), [(y0 - Y) / res, (X - x0) / res], order=1)
        k = np.where(v < 0.5)[0]
        if not len(k):
            out.append(float("nan")); continue
        # The white picket fence and its kerb: past the turf's edge (and the fence's dark shadow band) the first
        # bright pixel within 3 m; where none (a stand's dark front), the turf's edge itself.
        r0 = rs[k[0]]
        ro = np.arange(r0, r0 + 3.0, res / 2)
        Xo, Yo = C[0] + ro * math.sin(a), C[1] + ro * math.cos(a)
        lv = nd.map_coordinates(lum, [(y0 - Yo) / res, (Xo - x0) / res], order=1)
        j = np.where(lv > 1.25 * turf_lum)[0]
        out.append(float(ro[j[0]]) if len(j) else float(r0))
    return np.arange(0, 360, step), np.array(out), (im, x0, y0, res, keep)


if __name__ == "__main__":
    bs, r, extra = trace()
    json.dump({"bearing": bs.tolist(), "r": r.tolist(), "C": list(map(float, C))}, open(sys.argv[1], "w"))
    print("traced", np.isfinite(r).sum(), "of", len(r), "r %.1f..%.1f" % (np.nanmin(r), np.nanmax(r)))
    if len(sys.argv) > 2:
        from PIL import Image, ImageDraw
        im, x0, y0, res, keep = extra
        o = Image.fromarray(im); d = ImageDraw.Draw(o)
        for b, rr in zip(bs, r):
            if np.isfinite(rr):
                x, y = C[0] + rr * math.sin(math.radians(b)), C[1] + rr * math.cos(math.radians(b))
                d.ellipse([(x - x0) / res - 3, (y0 - y) / res - 3, (x - x0) / res + 3, (y0 - y) / res + 3], fill=(255, 0, 255))
        o.save(sys.argv[2], quality=85)


def boundary_line(src, fence_r, bs, inside=(1.0, 14.0)):
    """The painted boundary line: on each bearing, the brightest thin stripe between `inside` m within the fence."""
    im, x0, y0, res = src
    lum = im.astype(float).mean(2)
    top = lum - nd.median_filter(lum, size=max(5, int(1.2 / res) | 1))
    out = []
    for b, rf in zip(bs, fence_r):
        if not np.isfinite(rf):
            out.append(float("nan")); continue
        rs = np.arange(rf - inside[1], rf - inside[0], res / 3)
        a = math.radians(b)
        X, Y = C[0] + rs * math.sin(a), C[1] + rs * math.cos(a)
        v = nd.map_coordinates(top, [(y0 - Y) / res, (X - x0) / res], order=1)
        k = int(np.argmax(v))
        out.append(float(rs[k]) if v[k] > 12 else float("nan"))
    return np.array(out)
