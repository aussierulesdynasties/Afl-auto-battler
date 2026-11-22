"""Brisbane clash, back: the Hyundai lettering sits in the maroon yoke and its box reaches below the yoke's
bottom edge, so the box fill came out gold and the yoke kept only its two corners. Read the yoke's edge off
the photo (ref/BRL_back.png, the cut's square: the first gold row in each column, fitted as one curve) and
redraw maroon above it, gold below, between the maroon side panels.
    python brl_back_yoke.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image

fn = 'design_BRL_back.png'
a = np.array(Image.open(fn).convert('RGBA'))
r = np.array(Image.open('ref/BRL_back.png').convert('RGB')).astype(int)
MAROON = np.array([0x71, 0x2A, 0x39])
GOLD = np.array([0xEC, 0xB9, 0x50])
pts = []
for x in range(600, 1390, 10):
    col = r[340:520, x]
    g = (col[:, 0] > 180) & (col[:, 1] > 120) & (col[:, 2] < 130)
    if g.any():
        pts.append((x, 340 + np.argmax(g)))
p = np.array(pts, float)
fit = np.polyfit(p[:, 0], p[:, 1], 3)
res = np.abs(np.polyval(fit, p[:, 0]) - p[:, 1])
print('yoke edge fit, worst residual', res.max().round(1), 'px')
for x in range(590, 1390):
    e = np.polyval(fit, x)
    for y in range(250, int(e) + 30):
        px = a[y, x]
        if px[3] == 0:
            continue
        f = np.clip(y + 1 - e, 0, 1)
        px[:3] = (MAROON * (1 - f) + GOLD * f).astype(np.uint8)
Image.fromarray(a).save(fn)
print('brl back yoke redrawn')
