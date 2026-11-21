"""data/<g>/prep/trees.json from the aerial's measured tree canopy (aerial = reference/measurement only, no pixels used).
Canopy = dark green aerial pixels (G > 1.02 R, G > 1.05 B, mean < 95), opened to drop specks. Trees on an 8 m jittered
grid wherever >= 50% of the 4 m disk around the point is canopy. python -E canopy_trees.py spec.json"""
import sys, json, numpy as np
from PIL import Image
from scipy.ndimage import binary_opening, uniform_filter
Image.MAX_IMAGE_PIXELS = None
sp = json.load(open(sys.argv[1])); name = sp['name']; D = 'data/%s/' % name
sj = json.load(open(D + 'sat.json')); H, MP = sj['half_m'], sj['m_per_px']
a = np.asarray(Image.open(D + 'sat.png').convert('RGB')).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
m = (g > r * 1.02) & (g > b * 1.05) & ((r + g + b) / 3 < 95)
m = binary_opening(m, iterations=2)
f = uniform_filter(m.astype(np.float32), int(8 / MP))   # canopy share in an ~8 m box
NE = sp['near_half_m']; rng = np.random.default_rng(7); S = 8.0
xs = np.arange(-NE + S / 2, NE, S); X, Y = np.meshgrid(xs, xs)
X = X + rng.uniform(-2.5, 2.5, X.shape); Y = Y + rng.uniform(-2.5, 2.5, Y.shape)
px = ((X + H) / MP).astype(int); py = ((H - Y) / MP).astype(int)
ok = (px >= 0) & (py >= 0) & (px < f.shape[1]) & (py < f.shape[0])
keep = np.zeros_like(ok); keep[ok] = f[py[ok], px[ok]] >= 0.5
nk = len(sp['tree_kinds'])
T = [[round(float(x), 1), round(float(y), 1), int(rng.integers(nk))] for x, y in zip(X[keep], Y[keep])]
old = json.load(open(D + 'prep/trees.json'))
json.dump(old, open(D + 'prep/trees_fill_old.json', 'w'))
json.dump(T, open(D + 'prep/trees.json', 'w'))
print('canopy share', round(float(m.mean()), 3), 'trees', len(T), 'was', len(old))
