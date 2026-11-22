import json, numpy as np
from PIL import Image, ImageDraw
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400, 1400), Image.BOX)).astype(float)
t0 = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)
G = s.reshape(-1, 3).mean(0) / t0.reshape(-1, 3).mean(0); t = t0 * G
B = json.load(open('data/peoplefirst/prep/buildings.json')); R = []
for b in B:
    P = np.array(b['p']); c = P.mean(0)
    if np.abs(c).max() > 680 or np.hypot(*c) < 160: continue
    Q = c + (P - c) * 0.7; m = Image.new('L', (1400, 1400)); ImageDraw.Draw(m).polygon([(x + 700, 700 - y) for x, y in Q], fill=1); m = np.asarray(m, bool)
    if m.sum() < 8: continue
    a, mo, raw = np.median(s[m], 0), np.median(t[m], 0), np.median(t0[m], 0)
    R.append((np.abs(a - mo).mean(), [int(v) for v in c], b['c'], [int(v) for v in a], [int(v) for v in mo], [int(v) for v in raw], b.get('roof_c')))
R.sort(key=lambda r: -r[0])
for r in R[:12]: print(r)
d = np.array([r[0] for r in R]); print('median', np.median(d)); print('signed mean (aerial-model):', np.mean([np.mean(np.array(r[3]) - np.array(r[4])) for r in R]))
