# per band: shift the traced polygon dx,dy in -3..3 m (0.5 m steps); score = |aerial mean inside - mean of a 2 m ring| (colour contrast).
# reports the best shift (= position error of the trace) and the contrast sign (lighter / darker / greyer than its surround).
import json, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
NEAR = 1500; SR = 0.5; X0, X1, Y0, Y1 = 80, 260, -50, 135
sat = Image.open('data/optus/sat.png').convert('RGB')
cr = ndi.gaussian_filter(np.asarray(sat.crop((int((X0+NEAR)/SR), int((NEAR-Y1)/SR), int((X1+NEAR)/SR), int((NEAR-Y0)/SR)))).astype(np.float32), (0.7, 0.7, 0))
L = cr.mean(2); RB = cr[..., 0] - cr[..., 2]; dark = L < 95   # trees and shadow do not vote
d = json.load(open('spec/optus_fc_hand.json'))
def mask(p, dx, dy):
    im = Image.new('L', (cr.shape[1], cr.shape[0])); ImageDraw.Draw(im).polygon([((x+dx-X0)/SR, (Y1-y-dy)/SR) for x, y in p], fill=1); return np.asarray(im) > 0
def score(p, dx, dy):
    m = mask(p, dx, dy); ring = ndi.binary_dilation(m, iterations=4) & ~m
    a, b = m & ~dark, ring & ~dark
    if a.sum() < 20 or b.sum() < 20: return 0, 0, 0
    dl = L[a].mean() - L[b].mean(); dr = RB[a].mean() - RB[b].mean(); return np.hypot(dl, dr), dl, dr
out = []
for kind in ('bands', 'planters'):
    for i, b in enumerate(d[kind]):
        best = max(((score(b['pts'], dx, dy), dx, dy) for dx in np.arange(-3, 3.01, 0.5) for dy in np.arange(-3, 3.01, 0.5)), key=lambda t: t[0][0])
        s0 = score(b['pts'], 0, 0)
        out.append((kind, i, b.get('tone'), best[1], best[2], s0[0], best[0][0], best[0][1], best[0][2]))
        print('%-8s %2d tone %s shift (%+.1f, %+.1f) m contrast %.1f -> %.1f  dL %+.1f d(r-b) %+.1f' % out[-1])
sh = [np.hypot(o[3], o[4]) for o in out]; print('position error: mean %.2f m, max %.2f m' % (np.mean(sh), max(sh)))
json.dump(out, open('_bandfit.json', 'w'), default=float)
