"""Hand-made harbour water tile (no photo pixels): tileable wind ripples from summed sine waves with integer
frequencies, written as tex/mv_water.png (colour) and tex/mv_water_n.png (tangent normal). One tile = 16 m."""
import numpy as np, os
from PIL import Image
N = 1024; rng = np.random.default_rng(7)
u = np.arange(N) / N; U, V = np.meshgrid(u, u)
h = np.zeros((N, N)); hx = np.zeros((N, N)); hy = np.zeros((N, N))
for k in range(60):                       # wind from roughly one direction, short chop on top
    a = rng.normal(0.4, 0.5); f = rng.integers(6, 40); fx, fy = round(f * np.cos(a)), round(f * np.sin(a))
    if fx == 0 and fy == 0: continue
    amp = 1.0 / np.hypot(fx, fy) ** 1.1; ph = rng.uniform(0, 2 * np.pi)
    arg = 2 * np.pi * (fx * U + fy * V) + ph
    h += amp * np.sin(arg); hx += amp * 2 * np.pi * fx * np.cos(arg); hy += amp * 2 * np.pi * fy * np.cos(arg)
h = (h - h.mean()) / h.std()
base = np.array([25, 50, 73], float)       # median of photo p5 water (director 2026-11-20)
col = base[None, None, :] * (1 + 0.20 * h[..., None])
col[..., 2] += 4 * h                       # crests a touch bluer
col = np.clip(col, 0, 255).astype(np.uint8)
s = 0.012; nx, ny = -hx * s, -hy * s; nz = np.ones_like(nx); L = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
nrm = np.stack([nx / L, ny / L, nz / L], 2) * 0.5 + 0.5
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex')
Image.fromarray(col).save(os.path.join(D, 'mv_water.png'))
Image.fromarray((nrm * 255).astype(np.uint8)).save(os.path.join(D, 'mv_water_n.png'))
print('water std', round(float(col.astype(float).std(axis=(0, 1)).mean()), 1), 'luma std', round(float(col.astype(float).mean(2).std()), 1))
