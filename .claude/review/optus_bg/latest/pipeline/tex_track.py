# Hand-made track bed: 3.4 m across (256 px) x 5.44 m along (410 px), 8 concrete sleepers at 0.68 m, ballast stones between.
import numpy as np, sys
from PIL import Image, ImageFilter
rng = np.random.default_rng(7); W, H = 256, 410; ppm = W / 3.4
img = np.zeros((H, W, 3), float)
# ballast: Voronoi-ish stones by jittered points, each stone its own grey-brown tone, dark gaps
gy, gx = np.mgrid[0:H, 0:W]
pts = rng.uniform([0, 0], [H, W], (7000, 2)); tone = rng.uniform(0.7, 1.2, 7000)
base = np.array([120, 117, 112]) / 255
best = np.full((H, W), 1e9); second = np.full((H, W), 1e9); idx = np.zeros((H, W), int)
for k, (py, px) in enumerate(pts):
    dy = np.minimum(abs(gy - py), H - abs(gy - py)); dx = np.minimum(abs(gx - px), W - abs(gx - px)); d = dy * dy + dx * dx
    m = d < best; second = np.where(m, best, np.minimum(second, d)); idx = np.where(m, k, idx); best = np.where(m, d, best)
edge = np.clip((np.sqrt(second) - np.sqrt(best)) / 1.6, 0, 1)
img[:] = base * tone[idx][..., None] * (0.45 + 0.55 * edge[..., None])
img *= (1 + 0.06 * rng.standard_normal((H, W, 1)))
# shoulders darker and dustier at the edges of the bed
sh = np.clip(1 - np.abs(gx - W / 2) / (W / 2), 0, 1); img *= (0.8 + 0.2 * np.sqrt(sh))[..., None]
# concrete sleepers 2.6 m x 0.26 m, pale grey, worn top, shadow on the far side
sl_w = int(2.6 * ppm); sl_h = int(0.26 * ppm); x0 = (W - sl_w) // 2
for s in range(8):
    y0 = int(s * H / 8 + (H / 8 - sl_h) / 2)
    blk = np.array([168, 165, 158]) / 255 * (1 + 0.04 * rng.standard_normal((sl_h, sl_w, 1)))
    img[y0:y0 + sl_h, x0:x0 + sl_w] = blk
    img[y0 + sl_h:y0 + sl_h + 3, x0:x0 + sl_w] *= 0.55
    for rx in (-0.8, 0.8):   # rail seats: dark fastening pads under each rail
        cx = int(W / 2 + rx * ppm); img[y0:y0 + sl_h, cx - 6:cx + 6] = np.array([60, 58, 56]) / 255
# rust stain along the rail lines
for rx in (-0.8, 0.8):
    cx = W / 2 + rx * ppm; img *= (1 - 0.18 * np.exp(-((gx - cx) / 9) ** 2))[..., None] * np.array([1, 0.96, 0.9])
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(sys.argv[1])
print('std', (np.clip(img, 0, 1) * 255).std())
