"""Hand-made km-scale suburb tile tex/mt/suburb_macro.png (1024 px = 4000 m, seamless). Multiplied over the far suburb so its
grain survives distance: neighbourhood patches (leafy, dense roofs, newer pale estates), parks and ovals, arterial roads ~900 m
apart, a few big school/industrial blocks. Writes suburb_macro.mean (linear mean). python -E py_mk_suburb_macro.py"""
import os, numpy as np
from PIL import Image, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(41); n = 1024; mpp = 4000 / n
yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
P = R.uniform(0, n, (60, 2)); TONES = np.array([(150, 170, 120), (176, 160, 150), (196, 180, 162), (160, 166, 140), (184, 170, 156)], np.float32)
pt = TONES[R.integers(0, len(TONES), len(P))] * R.uniform(0.94, 1.06, (len(P), 1))
best = np.full((n, n), 1e9, np.float32); a = np.zeros((n, n, 3), np.float32)
for (px, py), c in zip(P, pt):
    dx = (xx - px + n / 2) % n - n / 2; dy = (yy - py + n / 2) % n - n / 2; dd = dx * dx + dy * dy
    m = dd < best; best[m] = dd[m]; a[m] = c
for _ in range(14):   # parks and ovals
    cx, cy = R.uniform(0, n, 2); w, h = R.uniform(25, 70, 2)
    m = (np.abs((xx - cx + n / 2) % n - n / 2) < w / 2) & (np.abs((yy - cy + n / 2) % n - n / 2) < h / 2); a[m] = (118, 150, 92)
for _ in range(8):    # school / industrial blocks: big pale roofs
    cx, cy = R.uniform(0, n, 2); w, h = R.uniform(18, 45, 2)
    m = (np.abs((xx - cx + n / 2) % n - n / 2) < w / 2) & (np.abs((yy - cy + n / 2) % n - n / 2) < h / 2); a[m] = (200, 198, 192)
sp = int(900 / mpp)   # arterial roads, 3 px (~12 m), slightly wavy
for o in range(0, n, sp):
    off = (o + R.integers(-20, 20)) % n
    a[(np.abs(((xx - off - 6 * np.sin(yy / 90.0)) + n / 2) % n - n / 2) < 1.5)] = (128, 128, 126)
    a[(np.abs(((yy - off - 6 * np.sin(xx / 110.0)) + n / 2) % n - n / 2) < 1.5)] = (128, 128, 126)
a = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
a *= 1 + 0.05 * (R.random((n, n, 1)) - 0.5)
img = np.clip(a, 0, 255).astype(np.uint8)
Image.fromarray(img).save(os.path.join(H, 'tex', 'mt', 'suburb_macro.png'))
open(os.path.join(H, 'tex', 'mt', 'suburb_macro.mean'), 'w').write('%.4f' % float(((img / 255.0) ** 2.2).mean()))
print('ok', open(os.path.join(H, 'tex', 'mt', 'suburb_macro.mean')).read())
