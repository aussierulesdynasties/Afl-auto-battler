"""Hand-made bay water tile tex/mt/water.png (1024 px = 80 m, seamless) and its normal map water_n.png. Corio Bay on a
light breeze: wind ripple rows running across the wind, longer swell, wind-slick patches (smoother, lighter) and darker
gust cat's-paws. Colour is a multiplier around 1 (water colour comes from the vertex colour: shallow teal to deep blue).
Writes water.mean (linear mean). python -E py_mk_water.py"""
import os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(77); n = 1024
yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n * 2 * np.pi
def lownoise(k, cnt):   # seamless low-frequency noise: sum of integer-wavenumber cosines
    f = np.zeros((n, n), np.float32)
    for _ in range(cnt):
        a, b = R.integers(-k, k + 1, 2); f += np.cos(a * xx + b * yy + R.uniform(0, 6.3)) / max(1, abs(a) + abs(b))
    return (f - f.min()) / (f.max() - f.min())
h = np.zeros((n, n), np.float32)
for _ in range(14):   # wind ripples: wavelengths 1.5-4 m, crests roughly across a NW wind
    k = R.integers(20, 54); ang = R.normal(0.6, 0.25); a, b = int(round(k * np.cos(ang))), int(round(k * np.sin(ang)))
    h += np.sin(a * xx + b * yy + R.uniform(0, 6.3)) * R.uniform(0.4, 1.0) / k * 30
for _ in range(4):    # swell 10-20 m
    k = R.integers(4, 8); ang = R.normal(0.6, 0.15); a, b = int(round(k * np.cos(ang))), int(round(k * np.sin(ang)))
    h += np.sin(a * xx + b * yy + R.uniform(0, 6.3)) * 1.6
slick = lownoise(3, 9); gust = lownoise(5, 12)
amp = 0.35 + 0.9 * np.clip((gust - 0.35) * 2, 0, 1) * (1 - 0.7 * np.clip((slick - 0.6) * 3, 0, 1))
h *= amp
gy, gx = np.gradient(h); s = 0.9
nx, ny, nz = -gx * s, -gy * s, np.ones_like(h); L = np.sqrt(nx * nx + ny * ny + nz * nz)
Image.fromarray(np.stack([(nx / L * 0.5 + 0.5) * 255, (ny / L * 0.5 + 0.5) * 255, (nz / L * 0.5 + 0.5) * 255], 2).astype(np.uint8)).save(os.path.join(H, 'tex', 'mt', 'water_n.png'))
# colour: crest faces facing the sky lighter, troughs darker, slicks lighter, gust patches darker
c = 0.82 + 0.10 * np.tanh(h / (h.std() + 1e-6)) + 0.10 * np.clip((slick - 0.6) * 3, 0, 1) - 0.08 * np.clip((gust - 0.55) * 3, 0, 1)
c = np.clip(c, 0, 1)
rgb = np.stack([c * 0.97, c * 0.99, c], 2)
Image.fromarray((rgb * 255).astype(np.uint8)).save(os.path.join(H, 'tex', 'mt', 'water.png'))
open(os.path.join(H, 'tex', 'mt', 'water.mean'), 'w').write('%.4f' % float(((rgb) ** 2.2).mean()))
print('water mean', open(os.path.join(H, 'tex', 'mt', 'water.mean')).read())
