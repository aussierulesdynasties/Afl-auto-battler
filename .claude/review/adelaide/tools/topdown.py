"""Straight-down check: the Esri mosaic resampled onto the same world grid as the orthographic render (north up,
same scale), then the model drawn over it. TOP='cx,cy,size' as in render.py.
topdown.py render.png out.png  -> out.png (satellite | model edges on satellite | 50% blend) and out_sat.png"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esri import m2px
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cx, cy, sz = map(float, os.environ.get('TOP', '0,-10,400').split(','))
R = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(float); n = R.shape[0]
M = Image.open(os.path.join(ROOT, 'esri/mosaic.jpg')).convert('RGB')
# world coords of each output pixel centre, then the mosaic pixel (bilinear via PIL transform per pixel)
j, i = np.meshgrid(np.arange(n), np.arange(n))
X = cx - sz / 2 + (j + 0.5) * sz / n; Y = cy + sz / 2 - (i + 0.5) * sz / n
px = np.zeros_like(X); py = np.zeros_like(Y)
for a in range(n):
    for b in (0, n - 1):
        pass
# m2px is smooth: evaluate on a coarse grid and interpolate
g = np.linspace(0, n - 1, 33).astype(int)
from scipy.interpolate import RegularGridInterpolator
gx = np.array([[m2px(X[r, c], Y[r, c])[0] for c in g] for r in g]); gy = np.array([[m2px(X[r, c], Y[r, c])[1] for c in g] for r in g])
fx = RegularGridInterpolator((g, g), gx); fy = RegularGridInterpolator((g, g), gy)
pts = np.c_[i.ravel(), j.ravel()]
px = fx(pts).reshape(n, n); py = fy(pts).reshape(n, n)
from scipy.ndimage import map_coordinates
A = np.asarray(M).astype(float)
S = np.stack([map_coordinates(A[..., k], [py, px], order=1, mode='constant', cval=0) for k in range(3)], -1)
a = R[..., 3:4] / 255
edge = np.asarray(Image.fromarray(R[..., 3].astype(np.uint8)).filter(ImageFilter.FIND_EDGES)).astype(float)
lum = R[..., :3].mean(-1); le = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.FIND_EDGES)).astype(float)
E = ((edge > 40) | (le > 60))[..., None]
ov = np.where(E, [0, 255, 255], S)
bl = S * (1 - 0.5 * a) + R[..., :3] * 0.5 * a
out = np.concatenate([ov, bl], 1).clip(0, 255).astype(np.uint8)
Image.fromarray(out).save(sys.argv[2])
Image.fromarray(S.clip(0, 255).astype(np.uint8)).save(sys.argv[2].replace('.png', '_sat.png'))
