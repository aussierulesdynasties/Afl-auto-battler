"""House heights off Google Earth (2026-11-23). BELLERIVE_WORK=<dir> BELLERIVE_TERRAIN=<grid.npz>:
  python3 plan.py                                   # 5 points a house within 450 m -> hgt/plan5.json, points5.json
  node ge_hover.js $BELLERIVE_WORK/hgt/plan5.json $BELLERIVE_WORK/hgt/s5   # GE status bar at each point
  python3 read.py                                   # OCR -> hgt/heights5.json; merged into ../houses_ge.json
No imagery is kept in the repo, only the whole-metre readouts (houses_ge.json "ge_m": centre, ends, sides)."""
# OCR the readouts, then per house: gable/hip where the metre steps show it, and storeys from the ridge.
import json, os, re, subprocess, sys, numpy as np
from PIL import Image
S = os.path.join(os.environ['BELLERIVE_WORK'], 'hgt')
P = json.load(open(S + '/points5.json'))
T = np.load(os.environ['BELLERIVE_TERRAIN'])   # tools/grounds/terrain/grids/bellerive.npz
H = T['h_cm'] / 100.0           # rows south->north, step 2.5, half 1500
def ground(x, z):
    gx, gy = x + 2.98, -z - 1.02
    i, j = (gy + 1500) / 2.5, (gx + 1500) / 2.5
    i0, j0 = int(i), int(j); fi, fj = i - i0, j - j0
    return (H[i0, j0] * (1 - fi) * (1 - fj) + H[i0 + 1, j0] * fi * (1 - fj) + H[i0, j0 + 1] * (1 - fi) * fj + H[i0 + 1, j0 + 1] * fi * fj)
cache = S + '/ocr5.json'
ocr = json.load(open(cache)) if os.path.exists(cache) else {}
def read(name):
    if name in ocr: return ocr[name]
    f = S + '/s5/' + name + '.png'
    if not os.path.exists(f): return None
    im = Image.open(f); im.resize((im.width * 4, im.height * 4)).save('/tmp/ocr.png')
    t = subprocess.run(['tesseract', '/tmp/ocr.png', '-', '--psm', '7'], capture_output=True, text=True).stdout
    m = re.findall(r'(-?\d+)\s*m\b', t)
    ocr[name] = int(m[-1]) if m and 'Camera' in t else None
    return ocr[name]
GE_TURF = 10.0                       # GE's height of the turf (status bar); terrain grid turf = 0
res, stats = {}, {}
for name, e in P.items():
    v = {k: read(name + '__' + k) for k in ('c', 'e1', 'e2', 's1', 's2')}
    if any(x is None for x in v.values()): continue
    g = np.mean([ground(*p) for p in e['pts'].values()]) + GE_TURF
    c, ends, sides = v['c'], [v['e1'], v['e2']], [v['s1'], v['s2']]
    # Whole metres, so only clear steps count. A gable keeps the ridge's height out to both ends; a hip
    # drops at its ends as at its sides. Anything flatter than a metre's step stays unread (None).
    kind = None
    if max(sides) <= c - 1:
        if min(ends) >= c:
            kind = 'gable'
        elif max(ends) <= c - 1:
            kind = 'hip'
    ridge = c - g
    # storeys from the ridge and the sides together (a tree over the ridge reads high only at one point)
    eave = 5.6 if ridge >= 6.5 and np.mean(sides) - g >= 4.5 else 2.7
    res[e['key']] = {'kind': kind, 'eave': eave, 'ridge': round(float(ridge), 2), 'v': v}
    stats[str(kind)] = stats.get(str(kind), 0) + 1; stats['2st'] = stats.get('2st', 0) + (eave > 3)
json.dump(ocr, open(cache, 'w'))
json.dump(res, open(S + '/heights5.json', 'w'))
ev = np.array([r['eave'] for r in res.values()])
print(len(res), 'houses', stats, 'eave pct 10/50/90', np.percentile(ev, [10, 50, 90]).round(2) if len(ev) else None)
# Into houses_ge.json (run houses_ge.py first: it rewrites the file from the colour pass alone).
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'houses_ge.json')
g = json.load(open(G))
for k, v in res.items():
    if k in g:
        if v['kind']:
            g[k]['kind'] = v['kind']
        g[k]['eave'] = v['eave']; g[k]['ge_m'] = [v['v'][q] for q in ('c', 'e1', 'e2', 's1', 's2')]
json.dump(g, open(G, 'w'), separators=(',', ':'))
