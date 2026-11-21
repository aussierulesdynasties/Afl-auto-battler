"""Hand-made roof textures (no photo pixels). Grey multipliers (wall alpha 0: the roof's own colour times this).
One tile = 3.04 m square (four 760 mm sheets). roof_metal.png: trapezoidal ribs every 190 mm, sheet laps, fall-line grime,
blotches. roof_tile.png: terracotta courses 330 mm, tiles 260 mm wide, staggered, per-tile shade."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7); N = 512; mpp = 3.04 / N
x = np.arange(N) * mpp
# metal: rib profile across x (period 0.19 m): flat pan 0.86, rib crest 1.0 lit side, 0.70 shadow side
ph = (x % 0.19) / 0.19
rib = np.where(ph < 0.70, 0.86, np.where(ph < 0.80, 1.0, np.where(ph < 0.88, 0.93, 0.70)))
A = np.tile(rib[None, :], (N, 1))
sheet = (x // 0.76).astype(int); A *= (1 + 0.035 * (rng.random(4) - 0.5) * 2)[sheet % 4][None, :]   # sheet-to-sheet shade
lap = (np.abs((x + 0.0) % 0.76) < 0.012); A[:, lap] *= 0.78                                           # lap line
streak = rng.random((8, N)); streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255.0
A *= 1 - 0.07 * streak                                                                               # grime down the fall line
blot = np.asarray(Image.fromarray((rng.random((12, 12)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255.0
A *= 1 - 0.06 * blot
A *= 1 + 0.03 * (rng.random((N, N)) - 0.5)
def save(arr, name):
    g = np.clip(arr, 0, 1); rgba = np.zeros((N, N, 4)); rgba[..., :3] = g[..., None]; rgba[..., 3] = 0
    Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(out, name))
    print(name, 'grey std', round(float((g * 255).std()), 1), 'mean', round(float((g * 255).mean()), 1))
save(A, 'roof_metal.png')
# tile: rows (courses) 0.33 m along y, tiles 0.26 m along x, alternate courses offset half a tile
y = np.arange(N) * mpp
row = (y // 0.33).astype(int); fy = (y % 0.33) / 0.33
B = np.ones((N, N))
off = (row % 2)[:, None] * 0.13
tx = ((x[None, :] + off) // 0.26).astype(int); fx = ((x[None, :] + off) % 0.26) / 0.26
shade = rng.random((64, 64)); B *= 0.84 + 0.16 * shade[row[:, None] % 64, tx % 64]
B *= (0.80 + 0.20 * np.clip(fy[:, None] / 0.85, 0, 1))      # each course darker at its top edge (shadow of the course above)
B[(fx < 0.04) | (fx > 0.96)] *= 0.82                         # tile joints
B *= 1 - 0.05 * blot; B *= 1 + 0.03 * (rng.random((N, N)) - 0.5)
save(B, 'roof_tile.png')
