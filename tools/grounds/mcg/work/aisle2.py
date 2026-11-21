# Aisle finder on a stripzoom photo (50 px/deg): a column is an aisle where it is darker than its +-0.6 deg
# neighbourhood on most rows of the band. Prints bearings of the strongest such columns (>= mind deg apart).
# python work/aisle2.py strip_p.png b0 [frac] [mind]
import sys, numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d
p, b0 = sys.argv[1], float(sys.argv[2]); fr = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6; md = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
L = np.asarray(Image.open(p).convert('L'), float)[22:]
ok = L > 8
loc = uniform_filter1d(L, 60, axis=1); sm = uniform_filter1d(L, 7, axis=1)
dark = ((sm < loc - 3) & ok).sum(0) / np.maximum(ok.sum(0), 1)
dark[ok.sum(0) < 0.5 * L.shape[0]] = 0
dark = uniform_filter1d(dark, 9)
idx = np.argsort(-dark); pick = []
for i in idx:
    if dark[i] < fr: break
    if all(abs(i - j) > md * 50 for j in pick): pick.append(i)
bs = sorted(b0 + i / 50 for i in pick)
print(' '.join('%.1f:%.2f' % (b % 360, dark[int(round((b - b0) * 50))]) for b in bs))
