# Measured (aerial) vs model (top view) table for the People First background, 1400 x 1400 m at 1 m/px.
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400, 1400), Image.BOX)).astype(float)
t0 = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)
GAIN = s.reshape(-1, 3).mean(0) / t0.reshape(-1, 3).mean(0)   # render lighting vs satellite: one global gain per channel
t = np.clip(t0 * GAIN, 0, 255)
def px(p): return [(x + 700, 700 - y) for x, y in p]
def pmask(p):
    m = Image.new('L', (1400, 1400)); ImageDraw.Draw(m).polygon(px(p), fill=1); return np.asarray(m, bool)
rows = []
# water
def ws_(a):
    L = a.mean(2); sd = np.sqrt(np.clip(ndimage.uniform_filter(L**2, 7) - ndimage.uniform_filter(L, 7)**2, 0, None))
    smooth = ndimage.median_filter(sd, 5) < 4; low_gb = ndimage.median_filter(a[..., 1] - a[..., 2], 5) < 6   # water is smooth or blue-dark; canopy is rough and green
    return ndimage.binary_closing(ndimage.binary_opening((L < 60) & (a[..., 2] >= a[..., 0] - 4) & (smooth | low_gb), iterations=2), iterations=3)
def wm_(a): return (a[..., 2] > a[..., 0] + 25) & (a[..., 2] > a[..., 1] + 5)
W1, W2 = ws_(s), wm_(t0)
_bm = Image.new('L', (1400, 1400)); _d = ImageDraw.Draw(_bm)   # roofs and the stadium are not water in either image
for _b in json.load(open('data/peoplefirst/prep/buildings.json')): _d.polygon(px(_b['p']), fill=1)
_fr = json.load(open('data/peoplefirst/prep/footprint.json')); _d.polygon(px([(r * np.cos(np.radians(i * 360 / len(_fr))), r * np.sin(np.radians(i * 360 / len(_fr)))) for i, r in enumerate(_fr)]), fill=1)
_bm = ndimage.binary_dilation(np.asarray(_bm, bool), iterations=2); W1 &= ~_bm; W2 &= ~_bm
spec = json.load(open('spec/peoplefirst.json'))
court = np.zeros((1400, 1400), bool)
for k, p in spec['paint_poly']:
    if k == 'court_blue': court |= pmask(p)
W2 &= ~ndimage.binary_dilation(court, iterations=3)
rows.append(('Water area (m2)', int(W1.sum()), int(W2.sum()), 'IoU %.2f' % ((W1 & W2).sum() / (W1 | W2).sum())))
for i, (k, p) in enumerate([(q[0], [list(c) for c in list(__import__('shapely.geometry',fromlist=['Polygon']).Polygon(q[1]).buffer(4, join_style=2).exterior.coords)[:-1]]) for q in __import__('json').load(open('spec/peoplefirst_pre10c.json'))['paint_poly'] if q[0] == 'water']):
    m = pmask(p); rows.append(('Golf pond %d area (m2)' % (i + 1), int((m & W1).sum()), int((m & W2).sum()), 'model/aerial %.0f%% (original trace +4 m)' % (100 * (m & W2).sum() / max(1, (m & W1).sum()))))
# canopy (trees) per region: aerial trace vs model dark-green crowns
can = np.load('data/peoplefirst/prep/canopy.npy')[1500 * 2 - 1400:1500 * 2 + 1400, 1500 * 2 - 1400:1500 * 2 + 1400]
can = np.asarray(Image.fromarray(can.astype(np.uint8) * 255).resize((1400, 1400), Image.BOX)) > 127
L = t.mean(2); exg = 2 * t[..., 1] - t[..., 0] - t[..., 2]
RAD = {'ghost_gum': 4.6, 'red_gum': 7.0, 'paperbark': 4.2}; KN = spec['tree_kinds']
_ti = Image.new('L', (1400, 1400)); _td = ImageDraw.Draw(_ti)
for x, y, k in json.load(open('data/peoplefirst/prep/trees.json')):
    if abs(x) < 705 and abs(y) < 705: r = RAD[KN[int(k)]]; _td.ellipse([x + 700 - r, 700 - y - r, x + 700 + r, 700 - y + r], fill=1)
tm = np.asarray(_ti, bool)   # model crowns rasterised from the placed trees
regions = {'SW forest': (-700, -420, -400, 50), 'SE car park tree rows': (-280, -120, -380, -130), 'River bank N': (-150, 50, 450, 700), 'Golf course E': (420, 700, -350, 100), 'Whole 1.4 km': (-700, 700, -700, 700)}
for n, (x0, x1, y0, y1) in regions.items():
    sl = (slice(700 - y1, 700 - y0), slice(x0 + 700, x1 + 700))
    rows.append(('Tree cover %s' % n, '%.0f%%' % (100 * can[sl].mean()), '%.0f%%' % (100 * tm[sl].mean()), ''))
# roofs: median colour per footprint, aerial vs model
B = json.load(open('data/peoplefirst/prep/buildings.json')); d = []; n = 0
for b in B:
    P = np.array(b['p']); c = P.mean(0)
    if np.abs(c).max() > 680 or np.hypot(*c) < 160: continue
    Q = c + (P - c) * 0.7; m = pmask(Q.tolist())
    if m.sum() < 8: continue
    d.append((np.median(s[m], 0), np.median(t0[m], 0))); n += 1
_A = np.array([q[0] for q in d]); _M = np.array([q[1] for q in d]); _ok = _M.max(1) < 250   # fit roof gain on unsaturated roofs
RG = np.median(_A[_ok] / np.maximum(_M[_ok], 1), 0); d = np.abs(_A - np.clip(_M * RG, 0, 255)).mean(1)
rows.append(('Roof render-to-satellite gain (fitted on roofs)', '', ', '.join('%.2f' % g for g in RG), ''))
rows.append(('Roof colour, %d roofs: mean |RGB diff| (0-255)' % n, '', '%.1f' % d.mean(), 'within 25: %.0f%%' % (100 * (d < 25).mean())))
for k in ('court_blue', 'synth', 'synth_dark'):
    for kk, p in spec['paint_poly']:
        if kk == k:
            m = pmask(p); rows.append(('%s colour (RGB median)' % k, str([int(v) for v in np.median(s[m], 0)]), str([int(v) for v in np.median(t[m], 0)]), 'area %d m²' % m.sum()))
# whole-image overlay error: mean abs RGB difference after a 9 m blur
bs = ndimage.uniform_filter(s, (9, 9, 1)); bt = ndimage.uniform_filter(t, (9, 9, 1))
rows.append(('Render-to-satellite colour gain (R,G,B)', '', ', '.join('%.2f' % g for g in GAIN), 'applied to all model colours'))
rows.append(('Overlay error (9 m blur, mean |RGB diff|)', '', '%.1f' % np.abs(bs - bt).mean(), ''))
w = ['| Item | Aerial (measured) | Model | Note |', '|---|---|---|---|'] + ['| %s | %s | %s | %s |' % r for r in rows]
open('out/peoplefirst/meas_table.md', 'w', encoding='utf-8').write('\n'.join(w) + '\n'); print('\n'.join(w))
