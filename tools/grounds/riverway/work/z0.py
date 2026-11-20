# Draw the fitted fence ellipse projected into GE view v for a few field heights Z0 (crop panels) to calibrate Z0.
import sys, os, json, math, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import earthcam as E
v = sys.argv[1]; zs = [float(z) for z in sys.argv[2].split(',')]
x0, y0, a1, a2, rot = json.load(open('work/fence.json'))['ell']; t = np.radians(np.arange(0, 360, 1.0)); r = math.radians(rot)
X = np.stack([x0 + a1 * np.cos(t) * math.cos(r) - a2 * np.sin(t) * math.sin(r), y0 + a1 * np.cos(t) * math.sin(r) + a2 * np.sin(t) * math.cos(r)], 1)
d, tl = (320, 62) if v[0] == 'l' else (140, 72); c = E.cam(int(v[1:]), tl, d)
g = Image.open(f'ge/{v}.png').convert('RGB'); out = []
for z in zs:
    im = g.copy(); dr = ImageDraw.Draw(im)
    P = [tuple(E.proj(c, (x, y, z))) for x, y in X]; dr.line(P + [P[0]], fill=(255, 0, 255), width=1)
    im = im.crop((300, 250, 1620, 900)); ImageDraw.Draw(im).text((10, 10), f'Z0={z}', fill=(255, 255, 0)); out.append(im)
W = Image.new('RGB', (1320, 650 * len(out)))
for k, im in enumerate(out): W.paste(im, (0, 650 * k))
W.save(f'render/z0_{v}.jpg', quality=85)
