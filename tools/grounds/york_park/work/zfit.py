# Height of a plan patch: sample the satellite over a polar patch, project the patch at height z into GE views, correlate (gradient NCC).
# Z0=-3 python work/zfit.py b0 b1 r0 r1 views [zmin zmax dz]
import sys, math, numpy as np; sys.path.insert(0, 'work'); import gecam as G, earthcam as E
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
b0, b1, r0, r1 = (float(t) for t in sys.argv[1:5]); views = sys.argv[5].split(',')
zmin, zmax, dz = (float(t) for t in (sys.argv[6:9] if len(sys.argv) > 8 else (0, 40, 1)))
S = gaussian_filter(np.asarray(Image.open('sat/esri_025.png').convert('L'), float), 1.0)
B, R = np.meshgrid(np.arange(b0, b1, 0.15), np.arange(r0, r1, 0.25)); a = np.radians(B); X = R * np.sin(a); Y = R * np.cos(a)
s = map_coordinates(S, [(260 - Y) * 4, (X + 260) * 4], order=1)
def grad(m): gy, gx = np.gradient(m); return np.concatenate([gx.ravel(), gy.ravel()])
gs = grad(s); gs = (gs - gs.mean()) / gs.std()
for v in views:
    Gi = gaussian_filter(np.asarray(Image.open(f'ge/{v}.png').convert('L'), float), 0.7); c = G.cam(v); res = []
    for z in np.arange(zmin, zmax + 1e-6, dz):
        P = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z + G.Z0)], 1) - c['C']; w = P @ c['fwd']
        u = c['W'] / 2 + c['f'] * (P @ c['right']) / w; q = c['H'] / 2 - c['f'] * (P @ c['up']) / w
        g = map_coordinates(Gi, [q, u], order=1).reshape(X.shape); gg = grad(g); gg = (gg - gg.mean()) / (gg.std() + 1e-9)
        res.append((float((gs * gg).mean()), z))
    res.sort(reverse=True); print(v, ' '.join(f'z{z:g}:{n:.3f}' for n, z in res[:4]))
