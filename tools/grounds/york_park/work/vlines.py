# Draw vertical lines (z 0..zmax, ticks every 10 m) at plan points on a GE view.  Z0=-3 python work/vlines.py view "x,y;x,y.." scale out [zmax]
import sys, numpy as np; sys.path.insert(0, 'work'); import gecam as G
from PIL import Image, ImageDraw
v, pts, sc, out = sys.argv[1:5]; zmax = float(sys.argv[5]) if len(sys.argv) > 5 else 60
im = Image.open(f'ge/{v}.png').convert('RGB'); im = im.resize((int(im.size[0] * float(sc)), int(im.size[1] * float(sc))), Image.LANCZOS); d = ImageDraw.Draw(im); s = float(sc)
cols = [(255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 255, 0), (255, 128, 0), (128, 128, 255), (255, 255, 255)]
for k, p in enumerate(pts.split(';')):
    x, y = (float(t) for t in p.split(',')); A = G.P(v, [x, y, 0])[0] * s; B = G.P(v, [x, y, zmax])[0] * s
    d.line([tuple(A), tuple(B)], fill=cols[k % 8], width=1)
    for z in range(10, int(zmax) + 1, 10):
        q = G.P(v, [x, y, z])[0] * s; d.line([(q[0] - 3, q[1]), (q[0] + 3, q[1])], fill=cols[k % 8], width=1)
    d.text((B[0] + 3, B[1] - 10), str(k + 1), fill=cols[k % 8])
im.save(out, quality=90); print(out)
