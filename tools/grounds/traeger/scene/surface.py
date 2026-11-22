"""The near ground's surfaces, traced off Google Earth's straight-down views and painted fresh.

Google Earth is a measuring reference here, never a picture in the game: no pixel of it is drawn. What is
taken from it is a map of surfaces, the way a surveyor would trace one:

1. Every pixel of the mosaic (0.5 m) is sorted into one of K surface classes by colour (k-means in Lab):
   red earth, buff dry grass, irrigated turf, asphalt, concrete, gravel, courts and so on. Classes come out
   of the data, so Alice Springs' own surfaces set them.
2. What stands up off the ground is taken out: the canopies, their shade, the roofs (OpenStreetMap's
   footprints, moved by the view's lean). Their pixels take the class of the nearest open ground.
3. A majority filter tidies the edges (no single pixels), as a hand trace would.
4. Each class is painted in its own median colour, with its own measured grain: fBm noise at 6 m, 1.5 m and
   0.3 m scaled to the class's own spread, and the class's broad unevenness (patchy watering, worn tracks)
   from its tone averaged over 8 m.

The result is a painting of where each surface is, at any map's resolution.
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.ndimage import map_coordinates

import canopy

K_CLASSES = 22
R, K = canopy.R, canopy.K


def _lab(rgb):
    return cv2.cvtColor(np.ascontiguousarray(np.clip(rgb, 0, 255).astype(np.uint8)), cv2.COLOR_RGB2LAB).astype(np.float32)


def roof_mask(mos, buildings, storeys):
    """Every roof on the mosaic: its footprint where it stands and where the view's lean shows it."""
    H, W = mos.a.shape[:2]
    roof = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(roof)
    for t, p, wid in buildings:
        h = 3.6 * storeys(t, p, wid) + 1.0
        cx, cy = np.mean(p, 0)
        le, ln = mos.lean(cx, cy, h)
        for de, dn in ((0, 0), (le - cx, ln - cy)):
            d.polygon([mos.px(e + de, q + dn) for e, q in p], fill=255)
    return ndimage.binary_dilation(np.asarray(roof) > 0, iterations=2)


def canopy_mask(a, roofm):
    """Gum canopies: rough patches darker than the ground round them (a dark blob 2 to 10 m across), olive
    to grey-green but never the saturated green of turf, away from roofs, and not the smooth dark of shade."""
    Rr, G, B = a[..., 0], a[..., 1], a[..., 2]
    L = (Rr + G + B) / 3
    exg = 2 * G - Rr - B
    dog = ndimage.gaussian_filter(L, 7) - ndimage.gaussian_filter(L, 1.2)
    m = ndimage.uniform_filter(L, 5)
    tex = np.sqrt(np.maximum(ndimage.uniform_filter(L * L, 5) - m * m, 0))
    can = (dog > 6) & (exg > -4) & (exg < 60) & (L < 125) & (L > 18) & (tex > 5) & ((G - Rr) < 40)
    can &= ~((L < 60) & (tex < 7))                       # flat shade
    can &= ~ndimage.binary_dilation(roofm, iterations=4)  # roof edges and the shade at their feet
    can = ndimage.binary_opening(can, iterations=2)       # no thin lines (court lines, kerbs, fence shade)
    can = ndimage.binary_closing(can, iterations=2)
    lab, n = ndimage.label(can)
    sizes = ndimage.sum(can, lab, range(1, n + 1))
    return can & np.isin(lab, 1 + np.nonzero(sizes >= 24)[0])


class Surfaces:
    def __init__(self, mos, roofm, can):
        a = mos.a
        H, W = a.shape[:2]
        Rr, G, B = a[..., 0], a[..., 1], a[..., 2]
        L = (Rr + G + B) / 3
        m = ndimage.uniform_filter(L, 5)
        tex = np.sqrt(np.maximum(ndimage.uniform_filter(L * L, 5) - m * m, 0))
        # what stands up: canopies, shade, roofs
        shadow = (L < 58) & (np.max(a, -1) - np.min(a, -1) < 40)
        shadow = ndimage.binary_opening(shadow)
        shadow = ndimage.binary_dilation(shadow, iterations=1)
        self.standing = ndimage.binary_dilation(can, iterations=2) | shadow | roofm | ~mos.valid
        open_ = ~self.standing
        # classes from the open ground, in Lab
        labimg = _lab(a)
        rng = np.random.default_rng(7)
        ys, xs = np.nonzero(open_)
        pick = rng.choice(len(ys), min(300000, len(ys)), replace=False)
        sample = labimg[ys[pick], xs[pick]].astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.2)
        _, _, cent = cv2.kmeans(sample, K_CLASSES, None, crit, 4, cv2.KMEANS_PP_CENTERS)
        self.cent = cent
        lab = np.zeros((H, W), np.int16)
        for r0 in range(0, H, 96):
            blk = labimg[r0:r0 + 96].reshape(-1, 3)
            dd = ((blk[:, None, :] - cent[None]) ** 2).sum(-1)
            lab[r0:r0 + 96] = dd.argmin(1).reshape(-1, W)
        # standing things take the nearest open ground's class
        idx = ndimage.distance_transform_edt(self.standing, return_distances=False, return_indices=True)
        lab = lab[idx[0], idx[1]]
        # majority filter, 2.5 m
        best = np.zeros((H, W), np.float32)
        out = lab.copy()
        for k in range(K_CLASSES):
            f = ndimage.uniform_filter((lab == k).astype(np.float32), 5)
            sel = f > best
            out[sel] = k
            best[sel] = f[sel]
        self.lab = out
        # each class: median colour and grain, from its open pixels only
        self.col = np.zeros((K_CLASSES, 3), np.float32)
        self.grain = np.zeros(K_CLASSES, np.float32)
        hp = L - ndimage.gaussian_filter(L, 3)
        for k in range(K_CLASSES):
            sel = (out == k) & open_
            if sel.sum() < 50:
                sel = out == k
            if sel.sum() == 0:
                continue
            self.col[k] = np.median(a[sel], 0)
            self.grain[k] = float(np.clip(np.std(hp[sel]), 2.0, 16.0))
        # broad unevenness: each class's tone over 8 m against its median, from open pixels
        Lc = (self.col.mean(1))[out]
        ratio = np.where(open_, L / np.maximum(Lc, 1), 0)
        w = ndimage.gaussian_filter(open_.astype(np.float32), 8)
        r = ndimage.gaussian_filter(ratio.astype(np.float32), 8) / np.maximum(w, 1e-3)
        self.ratio = np.clip(np.where(w > 0.05, r, 1.0), 0.8, 1.2).astype(np.float32)
        self.base = self.col[out] * self.ratio[..., None]
        print("surfaces:", K_CLASSES, "classes;", f"{self.standing.mean():.0%} under standing things")

    def paint(self, cv, seed=11):
        """The ground for a paint.Canvas: the class colours at the canvas' resolution, with grain."""
        E, N = cv.grid()
        px, py = (E + R) * K - 0.5, (R - N) * K - 0.5
        img = np.stack([map_coordinates(self.base[..., c], [py, px], order=1, mode="nearest")
                        for c in range(3)], -1)
        labs = map_coordinates(self.lab.astype(np.float32), [py, px], order=0, mode="nearest").astype(int)
        amp = self.grain[labs]
        mpp = 1.0 / cv.k
        n = np.zeros(E.shape, np.float32)
        rng = np.random.default_rng(seed)
        for scale, wgt in ((6.0, 0.55), (1.5, 0.35), (0.3, 0.25)):
            if scale < 1.2 * mpp:
                continue
            cells = max(2, int(round(cv.size * mpp / scale)))
            g = rng.standard_normal((cells, cells)).astype(np.float32)
            n += wgt * cv2.resize(g, (cv.size, cv.size), interpolation=cv2.INTER_CUBIC)
        n += 0.35 * rng.standard_normal(E.shape).astype(np.float32)     # the finest grit, per pixel
        img = img + (amp * n)[..., None] * np.array([1.0, 0.96, 0.9], np.float32)
        return img

