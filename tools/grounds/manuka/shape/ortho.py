"""The aerial photo (Esri World Imagery, zoom 19) resampled onto Manuka's frame, for measuring only: it stays in the
cache and is never committed or baked into a texture (docs/DATA_SOURCES.md).

    ortho(r, res) -> (img HxWx3 uint8, x0, y0, res): pixel (i, j) is at x = x0 + j*res, y = y0 - i*res.
"""
import math
import os
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "town"))
from common import CACHE, C, latlon  # noqa: E402


def ortho(r=115.0, res=0.1, z=19, cx=None, cy=None):
    from PIL import Image
    cx = C[0] if cx is None else cx
    cy = C[1] if cy is None else cy
    out = os.path.join(CACHE, "ortho_z%d_%d_%d_%d_%g.npy" % (z, cx, cy, r, res))
    if os.path.exists(out):
        return np.load(out), cx - r, cy + r, res
    d = os.path.join(CACHE, "img%d" % z)
    os.makedirs(d, exist_ok=True)
    n = 2 ** z

    def txy(lat, lon):
        return ((lon + 180) / 360 * n, (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n)
    xs = cx - r + np.arange(int(2 * r / res)) * res
    ys = cy + r - np.arange(int(2 * r / res)) * res
    X, Y = np.meshgrid(xs, ys)
    lat, lon = latlon(X, Y)
    tx, ty = txy(lat, lon)
    tiles = {}
    img = np.zeros(X.shape + (3,), np.uint8)
    ix, iy = np.floor(tx).astype(int), np.floor(ty).astype(int)
    for i in range(ix.min(), ix.max() + 1):
        for j in range(iy.min(), iy.max() + 1):
            p = os.path.join(d, "%d_%d_%d.jpg" % (z, i, j))
            if not os.path.exists(p):
                urllib.request.urlretrieve("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/%d/%d/%d"
                                           % (z, j, i), p)
            T = np.asarray(Image.open(p).convert("RGB"))
            m = (ix == i) & (iy == j)
            px = np.clip(((tx[m] - i) * T.shape[1]).astype(int), 0, T.shape[1] - 1)
            py = np.clip(((ty[m] - j) * T.shape[0]).astype(int), 0, T.shape[0] - 1)
            img[m] = T[py, px]
    np.save(out, img)
    return img, cx - r, cy + r, res


if __name__ == "__main__":
    from PIL import Image
    im, x0, y0, res = ortho()
    Image.fromarray(im).save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ortho.jpg")
    print(im.shape, x0, y0, res)
