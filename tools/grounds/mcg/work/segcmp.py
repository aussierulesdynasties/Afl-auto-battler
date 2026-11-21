# Photo (top) vs render (bottom) for one stretch of the outside, from one matched GE camera, with bearing lines
# every 2 deg at the footprint (z 0-30) and height lines every 5 m.  python work/segcmp.py b0 b1 view out.png [rpad]
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import earthcam
D = json.load(open(os.path.join(SP, 'model', 'mcg.json')))
C = json.load(open(os.path.join(HERE, 'cams.json')))


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def foot(b):
    best = 0
    for k in ('shane_warne', 'mcc', 'olympic', 'ponsford'):
        P = np.array(D['osm'][k], float); d = np.array(pol(b, 1.0))
        for a, c in zip(P, np.roll(P, -1, 0)):
            e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-9: continue
            t, s = np.linalg.solve(M, a)
            if t > 0 and 0 <= s <= 1: best = max(best, t)
    return best


b0, b1, v, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3], sys.argv[4]
pad = float(sys.argv[5]) if len(sys.argv) > 5 else 6
if b1 < b0: b1 += 360
x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
bs = np.arange(b0, b1 + 0.01, 0.5)
pts = []
for b in bs:
    r = foot(b % 360)
    for z in (0, 30): pts.append(earthcam.proj(c, (*pol(b, r + pad), z)))
    pts.append(earthcam.proj(c, (*pol(b, r - 25), 30)))
pts = np.array(pts)
X0, Y0 = pts.min(0) - 30; X1, Y1 = pts.max(0) + 30
X0, Y0 = max(0, X0), max(85, Y0); X1, Y1 = min(1920, X1), min(1050, Y1)
ims = []
for src in ('ge', 'rr'):
    im = Image.open(os.path.join(SP, src, v + '.png')).convert('RGBA')
    bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    dr = ImageDraw.Draw(im)
    for b in np.arange(math.ceil(b0 / 2) * 2, b1 + 0.01, 2):
        r = foot(b % 360) + pad
        p = [tuple(earthcam.proj(c, (*pol(b, r), z))) for z in (0, 30)]
        dr.line(p, fill=(255, 0, 255), width=1); dr.text(p[0], '%g' % (b % 360), fill=(255, 0, 255))
    for z in range(0, 31, 5):
        p = [tuple(earthcam.proj(c, (*pol(b, foot(b % 360) + pad), z))) for b in bs]
        dr.line(p, fill=(0, 255, 255), width=1); dr.text(p[-1], str(z), fill=(0, 255, 255))
    ims.append(im.crop((int(X0), int(Y0), int(X1), int(Y1))))
w, hh = ims[0].size; s = min(2.0, 1900 / w)
o = Image.new('RGB', (int(w * s), int(hh * s) * 2 + 6))
o.paste(ims[0].resize((int(w * s), int(hh * s))), (0, 0)); o.paste(ims[1].resize((int(w * s), int(hh * s))), (0, int(hh * s) + 6))
o.save(out); print(out, o.size)
