# Draw z=0 lines at set-backs 0,2,4,6,8 m inside the footprint, and z lines 2,3,4,5 at the footprint, on photo v.
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE); sys.path.insert(0, HERE)
import earthcam
from segcmp import foot, pol, C
b0, b1, v, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3], sys.argv[4]
x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
im = Image.open(os.path.join(SP, 'ge', v + '.png')).convert('RGB'); dr = ImageDraw.Draw(im)
bs = np.arange(b0, b1 + 0.01, 0.25); P = []
cols = {0: (255, 255, 0), 2: (0, 255, 0), 4: (0, 255, 255), 6: (255, 128, 0), 8: (255, 0, 0)}
for s, col in cols.items():
    p = [tuple(earthcam.proj(c, (*pol(b, foot(b) - s), 0))) for b in bs]; dr.line(p, fill=col, width=1); P += p
for z in (2, 3, 4, 5):
    p = [tuple(earthcam.proj(c, (*pol(b, foot(b)), z))) for b in bs]; dr.line(p, fill=(255, 0, 255), width=1); P += p
for b in np.arange(math.ceil(b0), b1 + 0.01, 1):
    p = [tuple(earthcam.proj(c, (*pol(b, foot(b)), z))) for z in (0, 6)]; dr.line(p, fill=(255, 255, 255), width=1); dr.text(p[0], '%g' % b, fill=(255, 255, 255))
P = np.array(P); X0, Y0 = P.min(0) - 40; X1, Y1 = P.max(0) + 40
cr = im.crop((int(X0), int(Y0), int(X1), int(Y1))); s = min(4, 1800 / cr.width); cr.resize((int(cr.width * s), int(cr.height * s)), Image.LANCZOS).save(out); print(out)
