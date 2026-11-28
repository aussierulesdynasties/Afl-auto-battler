# Draw a stand's roof edge (from model/york_park.json) at several heights on a GE view, to read its height.
# Z0=-3 python work/edgez.py view stand which(in|out) z1,z2,.. x0,y0,x1,y1 scale out
import sys, json, math, numpy as np; sys.path.insert(0, 'work'); import gecam as G
from PIL import Image, ImageDraw
v, st, wh, zs, box, sc, out = sys.argv[1:8]; zs = [float(z) for z in zs.split(',')]; x0, y0, x1, y1 = (int(t) for t in box.split(',')); sc = float(sc)
S = [s for s in json.load(open('model/york_park.json'))['stands'] if s['name'] == st][0]; T = np.array(S['roof'], float)
im = Image.open(f'ge/{v}.png').convert('RGB').crop((x0, y0, x1, y1)); im = im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.LANCZOS); d = ImageDraw.Draw(im)
cols = [(255, 0, 0), (255, 160, 0), (255, 255, 0), (0, 255, 0), (0, 200, 255), (255, 0, 255)]
for k, z in enumerate(zs):
    pts = []
    for b in np.linspace(T[0, 0], T[-1, 0], 60):
        r = np.interp(b, T[:, 0], T[:, 1 if wh == 'in' else 2]); a = math.radians(b)
        u, w = G.P(v, [r * math.sin(a), r * math.cos(a), z])[0]; pts.append(((u - x0) * sc, (w - y0) * sc))
    d.line(pts, fill=cols[k % 6], width=2); d.text((pts[0][0] + 4, pts[0][1]), f'{z:g}', fill=cols[k % 6])
im.save(out, quality=90); print(out)
