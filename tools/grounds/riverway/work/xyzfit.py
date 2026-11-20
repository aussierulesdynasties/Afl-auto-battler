# Joint fit of a plan shift (dx,dy) and height z for a satellite patch against several GE views (sum of gradient NCC).
# Z0=-3 python work/xyzfit.py b0 b1 r0 r1 views span step zmin zmax zstep [sigma]
import sys, math, numpy as np; sys.path.insert(0, 'work'); import gecam as G
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
b0, b1, r0, r1 = (float(t) for t in sys.argv[1:5]); views = sys.argv[5].split(',')
span, st, zmin, zmax, zst = (float(t) for t in sys.argv[6:11]); sg = float(sys.argv[11]) if len(sys.argv) > 11 else 1.5
S = gaussian_filter(np.asarray(Image.open('sat/esri_025.png').convert('L'), float), sg * 2)
B, R = np.meshgrid(np.arange(b0, b1, 0.3), np.arange(r0, r1, 0.5)); a = np.radians(B); X = R * np.sin(a); Y = R * np.cos(a)
s = map_coordinates(S, [(260 - Y) * 4, (X + 260) * 4], order=1)
def grad(m): gy, gx = np.gradient(m); v = np.concatenate([gx.ravel(), gy.ravel()]); return (v - v.mean()) / (v.std() + 1e-9)
gs = grad(s)
IM = {v: gaussian_filter(np.asarray(Image.open(f'ge/{v}.png').convert('L'), float), sg) for v in views}; CM = {v: G.cam(v) for v in views}
best = []
import os; DX0 = float(os.environ.get("DX0", 0)); DY0 = float(os.environ.get("DY0", 0))
for dx in DX0 + np.arange(-span, span + 1e-6, st):
    for dy in DY0 + np.arange(-span, span + 1e-6, st):
        for z in np.arange(zmin, zmax + 1e-6, zst):
            tot = []; 
            for v in views:
                c = CM[v]; P = np.stack([X.ravel() + dx, Y.ravel() + dy, np.full(X.size, z + G.Z0)], 1) - c['C']; w = P @ c['fwd']
                u = c['W'] / 2 + c['f'] * (P @ c['right']) / w; q = c['H'] / 2 - c['f'] * (P @ c['up']) / w
                tot.append(float((gs * grad(map_coordinates(IM[v], [q, u], order=1).reshape(X.shape))).mean()))
            best.append((sum(tot) / len(tot), dx, dy, z, tot))
best.sort(key=lambda t: -t[0])
for t in best[:6]: print(f'ncc {t[0]:.3f} dx {t[1]:+.1f} dy {t[2]:+.1f} z {t[3]:.1f} ', ' '.join(f'{n:.2f}' for n in t[4]))
