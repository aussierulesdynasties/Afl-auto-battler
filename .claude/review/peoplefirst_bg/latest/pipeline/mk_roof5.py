"""Membrane look on big flat roofs: seams every 2 m with shadow, ponding stains, walk pads; staining also on the shed sheet. Tileable."""
import numpy as np
from PIL import Image, ImageFilter
R = np.random.default_rng(5)
def stains(n, k, rmax):
    st = Image.new('L', (n, n), 0); from PIL import ImageDraw; d = ImageDraw.Draw(st)
    for _ in range(k):
        x, y = R.integers(0, n, 2); rx, ry = R.integers(rmax // 4, rmax, 2); v = int(R.integers(80, 200))
        for ox in (-n, 0, n):
            for oy in (-n, 0, n): d.ellipse([x - rx + ox, y - ry + oy, x + rx + ox, y + ry + oy], fill=v)
    return np.asarray(st.filter(ImageFilter.GaussianBlur(rmax / 3)), np.float32)[..., None] / 255
# solar: 48 m, 2048 px
a = np.asarray(Image.open('tex/roof_solar_pre5.png'), np.float32); n = a.shape[0]; px = n / 48.0
rgb = a[..., :3]; grey = (np.abs(rgb[..., 0] - rgb[..., 2]) < 12)[..., None]
mem = np.full_like(rgb, 214.0) * (0.95 + 0.05 * R.random((n, n, 1)))
for k in np.arange(0, 48, 2.0):
    j = int(k * px); mem[:, j:j + 2] = 238; mem[:, j + 2:j + 4] = 176          # lap seam: lit edge then shadow
for k in np.arange(0, 48, 12.0): mem[int(k * px):int(k * px) + 3, :] = 182   # cross seams
s = stains(n, 40, 140); mem = mem * (1 - 0.3 * s) + np.array([120, 112, 96]) * 0.3 * s
rgb = np.where(grey, mem, rgb)
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8)).save('tex/roof_solar.png')
# shed: 12 m, 1024 px -- add stains and sheet end laps every 6 m
a = np.asarray(Image.open('tex/roof_shed_pre5.png'), np.float32); n = a.shape[0]; rgb = a[..., :3]
s = stains(n, 10, 120); rgb = rgb * (1 - 0.28 * s) + np.array([130, 120, 100]) * 0.28 * s
for k in (0, 512): rgb[k:k + 4] *= 0.78
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8)).save('tex/roof_shed.png'); print('ok')
