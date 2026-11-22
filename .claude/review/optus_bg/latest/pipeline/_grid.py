# gridded aerial crop for hand digitising: _grid.py x0 x1 y0 y1 scale step out
import sys, numpy as np
from PIL import Image, ImageDraw
NEAR = 1500; SR = 0.5
x0, x1, y0, y1, S, st = map(float, sys.argv[1:7]); out = sys.argv[7]
sat = Image.open('data/optus/sat.png').convert('RGB')
im = sat.crop((int((x0 + NEAR) / SR), int((NEAR - y1) / SR), int((x1 + NEAR) / SR), int((NEAR - y0) / SR)))
im = im.resize((int(im.size[0] * S), int(im.size[1] * S)), Image.LANCZOS); d = ImageDraw.Draw(im)
px = lambda x: (x - x0) / SR * S; py = lambda y: (y1 - y) / SR * S
for x in np.arange(np.ceil(x0 / st) * st, x1, st):
    d.line([(px(x), 0), (px(x), im.size[1])], fill=(0, 255, 255), width=1); d.text((px(x) + 2, 2), '%d' % x, fill=(255, 255, 0))
for y in np.arange(np.ceil(y0 / st) * st, y1, st):
    d.line([(0, py(y)), (im.size[0], py(y))], fill=(0, 255, 255), width=1); d.text((2, py(y) + 2), '%d' % y, fill=(255, 255, 0))
if len(sys.argv) > 8:   # overlay traced polygons
    import json
    P = json.load(open(sys.argv[8]))
    for p in P.get('bands', []) + P.get('planters', []):
        pts = [(px(x), py(y)) for x, y in p['pts']]
        d.line(pts + [pts[0]], fill=(255, 0, 255) if p in P.get('bands', []) else (0, 255, 0), width=2)
im.save(out, quality=90)
