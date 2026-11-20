# Field height Z0 per GE view: the fence ellipse projected at Z0 should sit on the dark fence line; score = mean luminance
# along the projected curve (bearings away from the stand and trees: 300-360, 0-60 and 90-130), lowest wins.
import sys, os, json, math, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import earthcam as E
x0, y0, a1, a2, rot = json.load(open('work/fence.json'))['ell']; r = math.radians(rot)
t = np.radians(np.arange(0, 360, 0.5))
X = np.stack([x0 + a1 * np.cos(t) * math.cos(r) - a2 * np.sin(t) * math.sin(r), y0 + a1 * np.cos(t) * math.sin(r) + a2 * np.sin(t) * math.cos(r)], 1)
for v in sys.argv[1:]:
    d, tl = (320, 62) if v[0] == 'l' else (140, 72); c = E.cam(int(v[1:]), tl, d)
    L = np.asarray(Image.open(f'ge/{v}.png').convert('L'), float); H, W = L.shape; best = []
    for z in np.arange(-12, 12.01, 0.25):
        P = np.array([E.proj(c, (x, y, z)) for x, y in X]); ok = (P[:, 0] > 5) & (P[:, 0] < W - 5) & (P[:, 1] > 90) & (P[:, 1] < H - 40)
        if ok.sum() < 50: continue
        best.append((L[P[ok, 1].astype(int), P[ok, 0].astype(int)].mean(), z))
    best.sort(); print(v, 'Z0', best[0][1], 'lum', round(best[0][0], 1), 'next', [b[1] for b in best[1:4]])
