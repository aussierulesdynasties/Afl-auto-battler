"""Measured bay colour field: median-ish (box-normalised) colour of the reference aerial's water pixels (sat_far.png,
30 m/px) smoothed over ~450 m, so shallows, sand banks and channels keep their real tone; land gaps filled from the
nearest water. -> data/gmhba/water_col.npy (sRGB float, 2000x2000, row 0 = north). python -E py_mk_watercol.py"""
import os, numpy as np
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'gmhba')
a = np.asarray(Image.open(os.path.join(D, 'sat_far.png'))).astype(np.float64); lu = np.load(os.path.join(D, 'landuse.npy'))
w = (lu == 3).astype(np.float64)
def box(x, r):
    k = 2 * r + 1; p = np.pad(x, r, mode='edge'); c = np.pad(p.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k])
out = np.zeros_like(a); ww = w.copy()
for r in (7, 20, 60, 200):   # widen until every cell has water nearby
    bw = box(w, r); f = np.stack([box(a[..., c] * w, r) / np.maximum(bw, 1e-6) for c in range(3)], -1)
    m = (bw > 3) & (out.sum(2) == 0); out[m] = f[m]
np.save(os.path.join(D, 'water_col.npy'), out.astype(np.float32))
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1000, 1000)).save(os.path.join(D, 'water_col_prev.png'))
print('water colour mean', out[lu == 3].mean(0).round(1), 'p10/p90 lum', np.percentile(out[lu == 3].mean(1), [10, 90]).round(1))
