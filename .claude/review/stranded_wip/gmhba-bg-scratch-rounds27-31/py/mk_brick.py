"""Hand-made brick facade for houses: wall.png's windows (alpha) kept; brick courses 0.086 m, bricks 0.24 m, mortar lines, per-brick tone."""
import numpy as np
from PIL import Image
w = np.asarray(Image.open('proto/tex/wall.png').convert('RGBA')).astype(float); N = w.shape[0]; r = np.random.default_rng(5)
y, x = np.mgrid[0:N, 0:N].astype(float); ch = N / (3.2 / 0.086); bw = N / (3.6 / 0.24)
row = (y // ch).astype(int); xs = x + (row % 2) * bw / 2; col = (xs // bw).astype(int)
tone = r.uniform(0.8, 1.08, (row.max() + 2, col.max() + 2))[row, col]
mort = ((y % ch) < 1.1) | ((xs % bw) < 1.1)
v = np.where(mort, 1.25, tone) * (0.95 + 0.05 * r.random((N, N)))
rgb = np.clip(v * 214, 0, 255)
a = w[..., 3]; out = np.dstack([np.where(a[..., None] > 127, w[..., :3], rgb[..., None].repeat(3, 2)), a]).astype(np.uint8)
Image.fromarray(out, 'RGBA').save('proto/tex/house_wall.png'); print('std', round(float(rgb[a < 128].std()), 1))
