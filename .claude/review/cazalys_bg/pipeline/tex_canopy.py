"""Hand-painted rainforest canopy tile (no photo pixels): 60 m square, 512 px, seamless. Grey multiplier, alpha 0.
Crowns 5-16 m: each a lit dome (lighter top-left) with a dark rim; gaps between crowns dark."""
import os, sys
import numpy as np
from PIL import Image
out = sys.argv[1]; N = 512; M = 60.0; mpp = M / N; rng = np.random.default_rng(5)
A = np.full((N, N), 0.55)
yy, xx = np.mgrid[0:N, 0:N] * mpp
for _ in range(260):
    cx, cy = rng.random(2) * M; r = rng.uniform(2.5, 8.0); tone = rng.uniform(0.78, 1.0)
    dx = (xx - cx + M / 2) % M - M / 2; dy = (yy - cy + M / 2) % M - M / 2   # wrap -> seamless
    q = np.hypot(dx, dy) / r; m = q < 1
    dome = tone * (0.80 + 0.20 * np.clip(1 - q, 0, 1)) * (1 + 0.10 * np.clip((-dx - dy) / (2 * r), -1, 1))
    dome *= np.where(q > 0.85, 0.85, 1.0)
    A[m] = dome[m]
lump = rng.random((N // 8, N // 8)); lump = np.asarray(Image.fromarray((lump * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC)) / 255.0
A *= 0.94 + 0.06 * lump
A = np.clip(A, 0, 1); g = (A * 255).astype(np.uint8)
rgba = np.zeros((N, N, 4), np.uint8); rgba[..., :3] = g[..., None]
Image.fromarray(rgba, 'RGBA').save(os.path.join(out, 'canopy.png')); print('canopy mean', A.mean().round(3), 'std', A.std().round(3))
