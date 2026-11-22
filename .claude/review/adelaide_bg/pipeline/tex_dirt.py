# hand-made dry skinned-outfield dirt grain for Adelaide Oval No.2 (numpy only, tileable): tex/adl_dry_grain.png, 1024 px = 6 m
import numpy as np, os
from PIL import Image
n = 1024; rng = np.random.default_rng(21)
def band(lo, hi):   # periodic noise with features lo..hi px (FFT band-pass), unit std
    f = np.fft.fft2(rng.normal(size=(n, n))); k = np.hypot(*np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n)))
    m = (k > 1 / hi) & (k < 1 / lo); r = np.real(np.fft.ifft2(f * m)); return r / r.std()
v = 0.045 * band(120, 600) + 0.035 * band(20, 120) + 0.05 * band(2, 8) + 0.05 * rng.normal(size=(n, n))   # blotches, clods, grain, sand
spk = rng.random((n, n)); v -= 0.18 * (spk > 0.996); v += 0.12 * (spk < 0.003)   # dark crumbs, pale grit
warm = 0.03 * band(60, 300)   # slight red / yellow drift
base = np.array([168, 150, 112], float)
img = base[None, None] * (1 + v)[..., None]
img[..., 0] *= 1 + warm; img[..., 2] *= 1 - warm
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex', 'adl_dry_grain.png'))
print('mean', img.reshape(-1, 3).mean(0).round(1))
