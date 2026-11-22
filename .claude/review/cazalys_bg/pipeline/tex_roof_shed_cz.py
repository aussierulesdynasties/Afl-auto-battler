"""Hand-painted shed roof for Cazalys commercial roofs (no photo pixels): 12 m tile, 1024 px, grey multiplier, alpha 0.
Trapezoid ribs every 0.76 m (lit crest, deep shadow flank), sheet ends every 6 m, two rows of skylight sheets,
rust/grime streaks down the fall, patchy weathering."""
import numpy as np
from PIL import Image
n, M = 1024, 12.0; px = n / M; rng = np.random.default_rng(9)
def noise(cells, seed):
    r = np.random.default_rng(seed).random((cells, cells)); g = np.arange(n) / n * cells
    i = np.floor(g).astype(int); f = g - i; f = f * f * (3 - 2 * f)
    a = r[np.ix_(i % cells, i % cells)]; b = r[np.ix_(i % cells, (i + 1) % cells)]; c = r[np.ix_((i + 1) % cells, i % cells)]; d = r[np.ix_((i + 1) % cells, (i + 1) % cells)]
    return (a * (1 - f[None]) + b * f[None]) * (1 - f[:, None]) + (c * (1 - f[None]) + d * f[None]) * f[:, None]
x = (np.arange(n) + 0.5) / px; ph = (x % 0.76) / 0.76
rib = np.where(ph < 0.06, 1.0, np.where(ph < 0.12, 0.97, np.where(ph < 0.20, 0.66, 0.86)))
A = np.tile(rib[None], (n, 1)).astype(float)
for yy in (0.0, 6.0): r0 = int(yy * px); A[r0:r0 + 3] *= 0.72                         # sheet end laps
grime = noise(48, 2)[:, :]; streak = np.asarray(Image.fromarray((rng.random((6, n)) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)) / 255.0
A *= 1 - 0.16 * np.clip(streak - 0.45, 0, 1) * 2                                     # fall-line streaks
A *= 0.84 + 0.16 * (0.6 * noise(3, 4) + 0.4 * noise(9, 5))                           # patchy weathering
rgb = np.dstack([A, A, A])
rust = (noise(14, 7) > 0.78)[..., None] * (rib[None, :, None] < 0.9)
rgb = np.where(rust, rgb * np.array([0.92, 0.78, 0.66]), rgb)                         # rust bloom in the pans
for cx in (2.28, 8.36):                                                               # skylight sheets, one rib bay wide
    a, b = int(cx * px), int((cx + 0.76) * px)
    for y0 in (1.0, 7.0):
        c, d = int(y0 * px), int((y0 + 3.6) * px)
        rgb[c:d, a:b] = np.array([0.80, 0.86, 0.84]) * (0.92 + 0.08 * noise(5, 8)[c:d, a:b, None])
        rgb[c:d, a:a + 2] *= 0.6; rgb[c:d, b - 2:b] *= 0.6
alpha = np.zeros((n, n))
Image.fromarray(np.dstack([np.clip(rgb * 255, 0, 255), alpha]).astype(np.uint8), 'RGBA').save('tex/roof_shed_cz.png')
print('shed_cz mean', A.mean().round(3))
