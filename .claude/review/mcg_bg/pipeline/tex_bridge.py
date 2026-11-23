# Hand-made concrete bridge, 512 x 256 px = 12 m along x 6 m: cast panels, expansion joints, form-tie dots, weathering streaks.
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(5); W, H = 512, 256; ppm = W / 12.0
gy, gx = np.mgrid[0:H, 0:W].astype(float)
img = np.ones((H, W, 3)) * np.array([150, 147, 140]) / 255
img *= (1 + 0.05 * np.asarray(Image.fromarray((rng.random((32, 64)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float)[..., None] / 255 - 0.025)
pan = (gx // (3 * ppm)).astype(int); img *= (1 + 0.05 * rng.standard_normal(5)[pan])[..., None]   # 3 m cast panels
img[(gx % (3 * ppm)) < 2] *= 0.75
img[gx < 4] *= 0.4; img[gx > W - 4] *= 0.4                                      # expansion joint each 12 m
for yy in np.arange(0.5, 6, 1.0):
    for xx in np.arange(0.5, 12, 1.0):
        cy, cx = int(yy * ppm), int(xx * ppm); img[cy - 2:cy + 2, cx - 2:cx + 2] *= 0.72   # form-tie dots
for k in range(14):   # rain streaks down the face
    cx = rng.uniform(0, W); img *= (1 - rng.uniform(0.05, 0.15) * np.exp(-((gx - cx) / rng.uniform(3, 9)) ** 2) * (gy / H))[..., None]
img[:int(0.25 * ppm)] *= 0.8   # top edge kerb line
out = np.clip(img * 255, 0, 255).astype(np.uint8)
Image.fromarray(out).filter(ImageFilter.SMOOTH).save('tex/bridge_conc.png'); print('bridge', out.mean(axis=(0, 1)))
