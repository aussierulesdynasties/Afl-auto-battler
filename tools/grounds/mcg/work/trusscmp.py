# Photo (top) vs render (bottom) around the roof-top A-frame trusses visible in view v, each labelled with its bearing.
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE); sys.path.insert(0, HERE)
import earthcam
D = json.load(open(os.path.join(SP, 'model', 'mcg.json'))); C = json.load(open(os.path.join(HERE, 'cams.json')))
v, out = sys.argv[1], sys.argv[2]
x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
def per(tab):
    tb = np.array(tab, float); return lambda b: np.interp(b, np.r_[tb[:, 0] - 360, tb[:, 0], tb[:, 0] + 360], np.r_[tb[:, 1]] .repeat(1)[np.r_[np.arange(len(tb)), np.arange(len(tb)), np.arange(len(tb))]])
ro = per(D['roof_outer']); rh = per(D['roof_h']); T = D['trusses']
pts = []
for b in T['b']:
    r = ro(b) - 1; z = rh(b) + T['top']; A = math.radians(b)
    p = earthcam.proj(c, (r * math.sin(A), r * math.cos(A), z))
    if 0 < p[0] < 1920 and 90 < p[1] < 1050: pts.append((b, p))
if not pts: print('none'); sys.exit()
P = np.array([p for _, p in pts]); X0, Y0 = P.min(0) - 60; X1, Y1 = P.max(0) + 60
X0, Y0 = max(0, X0), max(85, Y0); X1, Y1 = min(1920, X1), min(1050, Y1)
ims = []
for src in ('ge', 'rr'):
    im = Image.open(os.path.join(SP, src, v + '.png')).convert('RGB'); dr = ImageDraw.Draw(im)
    for b, p in pts: dr.text((p[0] + 4, p[1] - 14), '%g' % b, fill=(255, 0, 255))
    ims.append(im.crop((int(X0), int(Y0), int(X1), int(Y1))))
w, hh = ims[0].size; s = min(2.0, 1900 / w)
o = Image.new('RGB', (int(w * s), int(hh * s) * 2 + 6))
o.paste(ims[0].resize((int(w * s), int(hh * s))), (0, 0)); o.paste(ims[1].resize((int(w * s), int(hh * s))), (0, int(hh * s) + 6))
o.save(out); print(out, o.size, [b for b, _ in pts])
