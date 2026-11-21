"""Hand-made big-shed roof (no photo pixels): one tile = 24.32 m square, 1024 px. Grey multiplier like roof_metal.png.
Ribs every 190 mm, a translucent skylight sheet (760 mm) every 6.08 m, end laps every 12.16 m, 10 m weathering patches."""
import os, sys
import numpy as np
from PIL import Image
out = sys.argv[1]; rng = np.random.default_rng(11); N = 1024; T = 24.32; mpp = T / N
x = np.arange(N) * mpp
ph = (x % 0.19) / 0.19
rib = np.where(ph < 0.70, 0.80, np.where(ph < 0.80, 0.92, np.where(ph < 0.88, 0.86, 0.66)))
A = np.tile(rib[None, :], (N, 1))
sky = (x % 6.08) < 0.76; A[:, sky] = 0.86 + 0.04 * rib[sky]          # skylight sheets run down the fall line
lap = (np.arange(N) * mpp % 12.16) < 0.10; A[lap, :] *= 0.90        # end laps across the roof
def noise(c, s): return np.asarray(Image.fromarray((np.random.default_rng(s).random((c, c)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255.0
A *= 1 + 0.03 * (rng.random((N, N)) - 0.5)
g = np.clip(A, 0, 1); rgba = np.zeros((N, N, 4)); rgba[..., :3] = g[..., None]
Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(os.path.join(out, 'roof_shed.png'))
print('roof_shed.png mean', round(float(g.mean() * 255), 1))
# weathering on its own tile (no direction), wraps seamlessly; scene.py breaks its repeat (2nd sample 0.37x, rot 36.87, 50/50, x1.414)
def wrapnoise(c, s):
    r = np.random.default_rng(s).random((c, c)); r = np.tile(r, (3, 3))
    big = np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize((3 * N, 3 * N), Image.BICUBIC)) / 255.0
    return big[N:2 * N, N:2 * N]
W = 1 - 0.14 * wrapnoise(3, 1) - 0.06 * wrapnoise(10, 2)
W = 0.5 + (W - W.mean()); Image.fromarray((np.clip(W, 0, 1) * 255).astype(np.uint8)).save(os.path.join(out, 'roof_shed_w.png'))
print('roof_shed_w.png mean', round(float(W.mean()), 3))
