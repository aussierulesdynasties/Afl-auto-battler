"""Hand-made replacements for the scene's procedural shader nodes (no photo pixels). Prints grey stddev per texture.
leaf_clumps.png  : tree crowns, was Voronoi F1 (scale 2.8, object space) -> MapRange 0..0.6 -> 1.15..0.62; stored /1.15. Tile = 8 cells = 8/2.8 m.
leaf_normal.png  : the matching bump (strength 0.6) as a tangent-space normal map.
court_grain.png  : court slabs, was Noise (scale 900, detail 4) -> MapRange 0.86..1.12; stored /1.25 (grain widened to meet grey std >= 10). Tile = 0.25 m."""
import os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(HERE, 'tex')
rng = np.random.default_rng(2808)
def enc(v):   # linear multiplier 0..1 -> sRGB 0..255 (Blender and glTF decode colour textures as sRGB)
    v = np.clip(v, 0, 1); return 255 * np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)

def save(nm, a):
    a = np.clip(np.round(a), 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(T, nm))
    g = a.astype(np.float32) if a.ndim == 2 else a[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114])
    print(nm, a.shape[1], 'x', a.shape[0], 'grey std %.1f' % g.std(), 'mean %.1f' % g.mean())

# --- leaf clumps: a 2D slice of a 3D voronoi (one jittered point per unit cell, like Blender's), tiling in x and y
N, PX = 8, 64; S = N * PX
pts = rng.random((N, N, 3, 3))           # [i, j, zlayer, xyz] jitter inside each cell; z layers -1, 0, +1 around the slice
zs = 0.5
u = (np.arange(S) + 0.5) / PX
X, Y = np.meshgrid(u, u)
d = np.full((S, S), 9.0)
for di in range(-1, 2):
    for dj in range(-1, 2):
        for k, zl in enumerate((-1, 0, 1)):
            ci = (np.floor(X).astype(int) + di); cj = (np.floor(Y).astype(int) + dj)
            p = pts[cj % N, ci % N, k]
            dx = ci + p[..., 0] - X; dy = cj + p[..., 1] - Y; dz = zl + p[..., 2] - zs
            d = np.minimum(d, np.sqrt(dx * dx + dy * dy + dz * dz))
mr = np.clip(1.15 + (0.62 - 1.15) * d / 0.6, 0.62, 1.15)
save('leaf_clumps.png', np.repeat(enc(mr / 1.15)[..., None], 3, 2))
# bump: height = distance (voronoi units); world gradient = 2.8 x per-unit gradient; strength 0.6
gy, gx = np.gradient(d, 1.0 / PX)
gx = np.roll(gx, 0); k = 0.3   # matched by eye to the old Bump node (strength 0.6), which rendered soft
n = np.stack([-gx * k, gy * k, np.ones_like(d)], -1)   # image rows run down = -v, so flip y
n /= np.linalg.norm(n, axis=-1, keepdims=True)
save('leaf_normal.png', (n * 0.5 + 0.5) * 255)

# --- court grain: periodic fBm (4 octaves), base frequency 900 / m over a 0.25 m tile = 225 cycles
S2 = 512; f = np.fft.fftfreq(S2) * S2
FX, FY = np.meshgrid(f, f); fr = np.hypot(FX, FY)
acc = np.zeros((S2, S2))
for o in range(4):
    c = 225 * 2 ** o / 4   # octaves straddle the base so the 512 px tile can hold them
    band = np.exp(-((fr - c) / (0.35 * c)) ** 2)
    w = np.real(np.fft.ifft2(np.fft.fft2(rng.normal(0, 1, (S2, S2))) * band))
    acc += 0.5 ** o * w / w.std()
acc /= acc.std()
mean = (0.86 + 0.26 * 0.5) / 1.25   # the old average multiplier 0.99, stored /1.25 (linear, headroom for the grain)
save('court_grain.png', np.repeat(enc(mean * (1 + 0.11 * acc))[..., None], 3, 2))
