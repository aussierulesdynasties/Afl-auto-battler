# _gridhi.py x0 x1 y0 y1 step out [polys.json]: grid + trace over the z19 plaza aerial (0.125 m/px, world x 80-260, y -50-135)
import sys, json, numpy as np
from PIL import Image, ImageDraw
R = 0.125; AX0, AY1 = 80, 135
x0, x1, y0, y1, st = map(float, sys.argv[1:6]); out = sys.argv[6]
im = Image.open('data/optus/sat_hi_enh.png').crop((int((x0 - AX0) / R), int((AY1 - y1) / R), int((x1 - AX0) / R), int((AY1 - y0) / R))); d = ImageDraw.Draw(im)
px = lambda x: (x - x0) / R; py = lambda y: (y1 - y) / R
for x in np.arange(np.ceil(x0 / st) * st, x1, st): d.line([(px(x), 0), (px(x), im.size[1])], fill=(0, 255, 255)); d.text((px(x) + 2, 2), '%d' % x, fill=(255, 255, 0))
for y in np.arange(np.ceil(y0 / st) * st, y1, st): d.line([(0, py(y)), (im.size[0], py(y))], fill=(0, 255, 255)); d.text((2, py(y) + 2), '%d' % y, fill=(255, 255, 0))
if len(sys.argv) > 7:
    P = json.load(open(sys.argv[7]))
    for k, c in (('bands', (255, 0, 255)), ('planters', (0, 255, 0))):
        for i, p in enumerate(P.get(k, [])):
            pts = [(px(x), py(y)) for x, y in p['pts']]; d.line(pts + [pts[0]], fill=c, width=2)
            cx, cy = np.mean(pts, 0); d.text((cx, cy), ('b%d' if k == 'bands' else 'p%d') % i, fill=c)
im.save(out, quality=90)
