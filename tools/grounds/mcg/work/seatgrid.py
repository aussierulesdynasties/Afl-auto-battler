# Bowl seating grid: photo (top) vs render (bottom) from one matched camera. Magenta = one radial line per bearing
# step down the model's tier profile (labelled every 5 deg), cyan = the model's tier breaks (row fronts/backs).
# python work/seatgrid.py view b0 b1 out.png [step] [scale]
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); import earthcam
D = json.load(open(os.path.join(SP, 'model', 'mcg.json'))); C = json.load(open(os.path.join(HERE, 'cams.json')))
def per(tab):
    t = np.array(sorted(tab), float); b = np.concatenate([t[:, 0] - 360, t[:, 0], t[:, 0] + 360])
    cols = [np.concatenate([t[:, k]] * 3) for k in range(1, t.shape[1])]
    return lambda q: [float(np.interp(q % 360, b, c)) for c in cols]
fb, ro, tiers = per(D['fence']), per(D['roof_outer']), per(D['tiers'])
def pol(b, r): a = math.radians(b); return (r * math.sin(a), r * math.cos(a))
def prof(b):
    rf = fb(b)[0]; rout = ro(b)[0]; d1, z1, d2, zb2, zt2, e2, z2, d3, zb3, zt3, zback, zfac = tiers(b)
    return [(rf + 1.5, -4.2), (rf + d1, z1), (rf + d2, zb2), (rf + d2 - 0.4, zt2), (rf + e2, z2), (rf + d3, zb3), (rf + d3 - 0.4, zt3), (rout - 8, zback)]
v, b0, b1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
st = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0; sc = float(sys.argv[6]) if len(sys.argv) > 6 else 2.0
if b1 < b0: b1 += 360
x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
P = lambda b, r, z: tuple(earthcam.proj(c, (*pol(b, r), z)))
bs = np.arange(b0, b1 + 1e-6, st)
pts = np.array([P(b, r, z) for b in bs for r, z in prof(b)])
X0, Y0 = np.maximum(pts.min(0) - 20, [0, 85]); X1, Y1 = np.minimum(pts.max(0) + 20, [1920, 1050])
ims = []
for src in ('ge', 'rr'):
    im = Image.open(os.path.join(SP, src, v + '.png')).convert('RGBA'); bg = Image.new('RGBA', im.size, (0, 0, 0, 255)); bg.alpha_composite(im)
    im = bg.convert('RGB').crop((int(X0), int(Y0), int(X1), int(Y1))); im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    dr = ImageDraw.Draw(im); Q = lambda p: ((p[0] - X0) * sc, (p[1] - Y0) * sc)
    for b in bs:
        pr = prof(b); L = [Q(P(b, r, z)) for r, z in pr]
        big = abs((b / 5) - round(b / 5)) < 1e-6
        if big: dr.line(L, fill=(255, 0, 255), width=1); dr.text(L[0], '%g' % (b % 360), fill=(255, 0, 255))
        else:
            for k in (1, 4, 7):  # short ticks at the top of each tier
                q = L[k]; dr.line([q, (q[0], q[1] + 6)], fill=(255, 255, 0), width=1)
    for k in range(8):
        dr.line([Q(P(b, *prof(b)[k])) for b in np.arange(b0, b1 + 1e-6, 0.5)], fill=(0, 255, 255), width=1)
    ims.append(im)
w, hh = ims[0].size; o = Image.new('RGB', (w, hh * 2 + 6)); o.paste(ims[0], (0, 0)); o.paste(ims[1], (0, hh + 6)); o.save(out); print(out, o.size)
