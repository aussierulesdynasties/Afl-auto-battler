"""Hand-made rail bed tile: 512 px across 2.8 m x 438 px along 2.4 m. Grey ballast stones, concrete sleepers every 0.6 m
(2.5 m long, 0.25 m wide), rust-brown stain between the rails. Writes tex/mt/rail_bed.png and its linear mean."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(11)
W, L = 512, 438; px = W / 2.8
a = np.full((L, W, 3), 120.0)
im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
for _ in range(9000):   # ballast stones 25-60 mm
    x, y = rng.uniform(0, W), rng.uniform(0, L); r = rng.uniform(0.012, 0.03) * px; v = int(rng.normal(128, 24))
    c = (v, v - 3, v - 8); pts = [(x + r * np.cos(t) * rng.uniform(0.7, 1.2), y + r * np.sin(t) * rng.uniform(0.7, 1.2)) for t in np.linspace(0, 2 * np.pi, 6, endpoint=False)]
    d.polygon(pts, fill=tuple(int(np.clip(q, 30, 230)) for q in c))
a = np.asarray(im).astype(float)
xx = np.arange(W)[None, :]; mid = np.exp(-((xx - W / 2) / (0.55 * px)) ** 2)[..., None]
a = a * (1 - 0.25 * mid) + np.array([110, 82, 60]) * 0.25 * mid   # rust stain between the rails
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
for k in range(4):
    y0 = (k * 0.6 + 0.175) * px * L / (2.4 * px) / (L / (2.4 * px)) * (L / 2.4); y1 = y0 + 0.25 * (L / 2.4)
    x0, x1 = (1.4 - 1.25) * px, (1.4 + 1.25) * px
    v = int(rng.normal(168, 6)); d.rectangle([x0, y0, x1, y1], fill=(v, v - 2, v - 6))
    d.line([x0, y1, x1, y1], fill=(70, 66, 60), width=2)   # shadow edge
im = im.filter(ImageFilter.GaussianBlur(0.6))
im.save(os.path.join(H, 'tex', 'mt', 'rail_bed.png'))
q = np.asarray(im) / 255.0; lin = np.where(q <= 0.04045, q / 12.92, ((q + 0.055) / 1.055) ** 2.4)
open(os.path.join(H, 'tex', 'mt', 'rail_bed.mean'), 'w').write('%.4f' % lin.mean())
print('rail_bed mean %.4f std %.1f' % (lin.mean(), np.asarray(im).astype(float).mean(-1).std()))
