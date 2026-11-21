# Unwrap the Esri satellite to bearing (x, 40 px/deg) by radius (y, 8 px/m, outward = down), grid every 1 deg / 2 m,
# current footprint (osm) in yellow.  python work/polsat.py b0 b1 r0 r1 out.png
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from segcmp_foot import foot
b0, b1, r0, r1, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
if b1 < b0: b1 += 360
S = np.asarray(Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('RGB'))
PX, PY = 40, 8
bs = b0 + np.arange(int((b1 - b0) * PX)) / PX; rs = r0 + np.arange(int((r1 - r0) * PY)) / PY
B, R = np.meshgrid(np.radians(bs), rs)
X = R * np.sin(B); Y = R * np.cos(B)
u = np.clip(((X + 260) * 4).astype(int), 0, 2079); v = np.clip(((260 - Y) * 4).astype(int), 0, 2079)
im = Image.fromarray(S[v, u]); d = ImageDraw.Draw(im)
for b in range(math.ceil(b0), int(b1) + 1):
    x = (b - b0) * PX; d.line([(x, 0), (x, im.height)], fill=(255, 0, 255) if b % 5 == 0 else (150, 0, 150), width=1)
    d.text((x + 2, 2), str(b % 360), fill=(255, 0, 255))
for r in range(math.ceil(r0 / 2) * 2, int(r1) + 1, 2):
    y = (r - r0) * PY; d.line([(0, y), (im.width, y)], fill=(0, 255, 255) if r % 10 == 0 else (0, 120, 120), width=1)
    d.text((2, y + 1), str(r), fill=(0, 255, 255))
d.line([((b - b0) * PX, (foot(b % 360) - r0) * PY) for b in bs[::4]], fill=(255, 255, 0), width=1)
im.save(out); print(out, im.size)
