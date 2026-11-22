# Hand-made large flat roof, 1024 px = 48 m square tile: standing-seam metal in 8 m bays, skylight strips, rooftop plant with shadows, drain stains.
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(11); N = 1024; ppm = N / 48.0
gy, gx = np.mgrid[0:N, 0:N].astype(float)
base = np.array([178, 180, 178]) / 255
img = np.ones((N, N, 3)) * base
bay = (gx // (8 * ppm)).astype(int)
img *= (1 + 0.07 * rng.standard_normal(bay.max() + 1)[bay])[..., None]          # each 8 m bay its own sheet batch
seam = (gx % (0.6 * ppm)) < 1.5; img[seam] *= 0.86                               # standing seams every 0.6 m
bayl = (gx % (8 * ppm)) < 3; img[bayl] *= 0.62                                    # bay laps read from far
img *= (1 + 0.035 * np.asarray(Image.fromarray((rng.random((64, 64)) * 255).astype(np.uint8)).resize((N, N), Image.BICUBIC), float)[..., None] / 255 - 0.0175)
for k in range(6):   # skylight strips: 1.2 m wide, 10 m long, pale translucent with dark frame
    x0 = int(((k % 3) * 16 + 3.4) * ppm); y0 = int((6 + (k // 3) * 24) * ppm); w = int(1.2 * ppm); h = int(10 * ppm)
    img[y0:y0 + h, x0:x0 + w] = np.array([206, 214, 212]) / 255
    img[y0:y0 + h, x0:x0 + 2] *= 0.5; img[y0:y0 + h, x0 + w - 2:x0 + w] *= 0.5
    img[y0 + h:y0 + h + 6, x0:x0 + w] *= 0.7
for k in range(9):   # plant: AC units and ducts, light boxes with a shadow to one side
    w, h = rng.uniform(1.5, 4.5, 2) * ppm; x0 = int(rng.uniform(1, 44) * ppm); y0 = int(rng.uniform(1, 44) * ppm)
    w, h = int(w), int(h)
    img[y0 + 5:y0 + h + 9, x0 + 5:x0 + w + 9] *= 0.6
    img[y0:y0 + h, x0:x0 + w] = np.array([150, 154, 156]) / 255 * rng.uniform(0.9, 1.1)
    img[y0:y0 + h:7, x0:x0 + w] *= 0.8
for k in range(5):   # drain stains: dark streaks running down-slope
    cx = rng.uniform(0, N); img *= (1 - 0.12 * np.exp(-((gx - cx) / 14) ** 2) * (gy / N))[..., None]
out = np.clip(img * 255, 0, 255).astype(np.uint8)
Image.fromarray(out).filter(ImageFilter.SMOOTH).save('tex/roof_big.png')
print('roof_big', out.mean(axis=(0, 1)))
