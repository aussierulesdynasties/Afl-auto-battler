# Prototype: trace forecourt ribbon bands from the aerial as vector polygons (reference only; no aerial pixel is kept).
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure
NEAR = 1500; SR = 0.5
b = json.load(open('data/optus/prep/forecourt.json'))
sat = Image.open('data/optus/sat.png').convert('RGB')
box = (int((b['x0'] + NEAR) / SR), int((NEAR - b['y1']) / SR), int((b['x1'] + NEAR) / SR), int((NEAR - b['y0']) / SR))
cr = np.asarray(sat.crop(box)).astype(np.float32) / 255
L = cr.mean(2); rb = cr[..., 0] - cr[..., 2]
green = (cr[..., 1] > cr[..., 0]) & (cr[..., 1] > cr[..., 2])
pave = (L > 0.42) & ~green & (cr.std(2) < 0.14)
# tones: 0 salmon base, 1 light ribbon (beige/grey, low red-blue), 2 dark red ribbon
sm = lambda x, s: ndi.gaussian_filter(x, s)
Ls, rbs = sm(L, 0.6), sm(rb, 0.6)
lab = np.zeros(L.shape, np.int8)
lab[(rbs < 0.08) & (Ls > 0.55)] = 1
lab[(rbs > 0.17) & (Ls < 0.60)] = 2
polys = {1: [], 2: []}
for k in (1, 2):
    f = sm(((lab == k) & pave).astype(np.float32), 1.2)
    for c in measure.find_contours(f, 0.5):
        if len(c) < 8: continue
        a = 0.5 * abs(np.dot(c[:, 0], np.roll(c[:, 1], 1)) - np.dot(c[:, 1], np.roll(c[:, 0], 1))) * SR * SR
        if a < 8: continue
        c = measure.approximate_polygon(c, 0.6)
        for _ in range(3):   # Chaikin corner cutting -> smooth crisp curve
            q = np.roll(c, -1, 0); c = np.concatenate([np.stack([0.75 * c + 0.25 * q, 0.25 * c + 0.75 * q], 1).reshape(-1, 2)])
        xy = np.column_stack([b['x0'] + c[:, 1] * SR, b['y1'] - c[:, 0] * SR])
        polys[k].append(xy.round(2).tolist())
json.dump(polys, open('data/optus/prep/fc_polys.json', 'w'))
print({k: len(v) for k, v in polys.items()})
# overlay check: outlines on the aerial, side by side with a flat fill
S = 3; W, H = cr.shape[1] * S, cr.shape[0] * S
ov = sat.crop(box).resize((W, H)); fl = Image.new('RGB', (W, H), (200, 140, 120)); d1 = ImageDraw.Draw(ov); d2 = ImageDraw.Draw(fl)
col = {1: (225, 215, 195), 2: (150, 70, 60)}
for k in (1, 2):
    for p in polys[k]:
        pts = [((x - b['x0']) / SR * S, (b['y1'] - y) / SR * S) for x, y in p]
        d1.line(pts + [pts[0]], fill=(0, 255, 255) if k == 1 else (255, 0, 255), width=2); d2.polygon(pts, fill=col[k])
im = Image.new('RGB', (W, 2 * H)); im.paste(ov, (0, 0)); im.paste(fl, (0, H)); im.save('_trace.jpg', quality=88)
