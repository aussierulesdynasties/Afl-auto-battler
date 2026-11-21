"""Hand-made along-the-road asphalt tile tex/mt/road_lane.png: 256 px across the road (u = 0 kerb .. 1 kerb) x 1024 px
along it (40 m). Aged Geelong street asphalt: darker wheel paths and a centre oil stain in each lane, lighter worn gutter
strip, rectangular patch repairs (fresh black and old faded), sealed cracks, the odd service-pit lid. Mean ~ the old road
tile (78,80,80). python -E py_mk_road_lane.py"""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = np.random.default_rng(23); W, L = 256, 1024
u = (np.arange(W) + 0.5) / W; v = np.arange(L)
a = np.full((L, W), 82.0)
for c in (0.18, 0.32, 0.68, 0.82): a -= 7 * np.exp(-((u - c) / 0.035) ** 2)[None]   # wheel paths
for c in (0.25, 0.75): a -= 5 * np.exp(-((u - c) / 0.03) ** 2)[None]                 # oil drip line mid-lane
a += 10 * np.exp(-(u / 0.035) ** 2)[None] + 10 * np.exp(-((1 - u) / 0.035) ** 2)[None]   # gutter edge, dusty and pale
a += R.normal(0, 4.5, (L, W)); a += np.repeat(R.normal(0, 3, L // 32), 32)[:, None]   # aggregate and resurfacing bands
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
for _ in range(9):   # patch repairs
    x0 = R.uniform(0.05, 0.7) * W; y0 = R.uniform(0, L - 120); w_ = R.uniform(0.12, 0.35) * W; h_ = R.uniform(25, 110)
    d.rectangle([x0, y0, min(W - 4, x0 + w_), y0 + h_], fill=int(R.choice([60, 66, 96, 100])))
for _ in range(14):  # sealed cracks: thin dark wandering lines
    x = R.uniform(0.1, 0.9) * W; y = R.uniform(0, L); pts = []
    for k in range(R.integers(6, 16)): x += R.normal(0, 4); y += R.uniform(4, 12); pts.append((x, y))
    d.line(pts, fill=48, width=1)
for _ in range(2):   # service pit lids
    x = R.uniform(0.15, 0.85) * W; y = R.uniform(20, L - 20); d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=112, outline=58)
im = im.filter(ImageFilter.GaussianBlur(0.6)); g = np.asarray(im).astype(float)
g = g * (78.0 / g.mean())
rgb = np.stack([g * 0.985, g, g], 2)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(H, 'tex', 'mt', 'road_lane.png')); print('ok', rgb.mean((0, 1)))
