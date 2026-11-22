# hand-made large-scale tiles (numpy, tileable FFT noise):
#  adl_patch60.png  1024 px = 60 m: worn/dry patch multiplier for Oval No.2 (grey, ~0.8-1.15 around 1 -> stored /1.25)
#  adl_solar.png    128 px = one 1.0 x 1.7 m panel: dark blue-black cells, pale aluminium frame
import numpy as np, os
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex'); R = np.random.default_rng(11)
def fnoise(n, s):
    f = np.fft.fft2(R.standard_normal((n, n)))
    ky, kx = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n), indexing='ij')
    im = np.real(np.fft.ifft2(f * np.exp(-(kx ** 2 + ky ** 2) * (np.pi * s) ** 2 / 2))); return im / im.std()
n = 1024
v = 1 + 0.07 * fnoise(n, 90) + 0.05 * fnoise(n, 30) + 0.025 * fnoise(n, 8)   # bare/worn blotches 10-60 m, tufts
v = np.clip(v, 0.75, 1.25)
Image.fromarray((v / 1.25 * 255).astype(np.uint8)).save(os.path.join(OUT, 'adl_patch60.png')); print('patch60', round(v.std(), 3))
n = 128; y, x = np.mgrid[0:n, 0:n] / n
rgb = np.zeros((n, n, 3)); rgb[:] = (28, 34, 52); rgb += 6 * fnoise(n, 20)[..., None]
cell = (np.abs(((x * 6) % 1) - 0.5) > 0.46) | (np.abs(((y * 10) % 1) - 0.5) > 0.46); rgb[cell] = (60, 66, 80)
fr = (x < 0.03) | (x > 0.97) | (y < 0.02) | (y > 0.98); rgb[fr] = (190, 192, 196)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'adl_solar.png')); print('solar')
