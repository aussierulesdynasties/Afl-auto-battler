# Per bearing: longest run of bright roof (lum > T) outside the fence -> roof inner / outer radius (m).
import os, json, math, sys
import numpy as np
from PIL import Image
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = np.asarray(Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('L')).astype(float)
F = dict(json.load(open(os.path.join(SP, 'work', 'fence.json')))['er'])
T = float(sys.argv[1]) if len(sys.argv) > 1 else 150
rows = []
for b in np.arange(0, 360, 2.0):
    a = math.radians(b); f = F[float(b)]; rs = np.arange(f + 1, f + 60, 0.25)
    u = ((rs * math.sin(a) + 260) * 4).astype(int); v = ((260 - rs * math.cos(a)) * 4).astype(int)
    L = np.array([np.median(S[max(0, vv - 2):vv + 3, max(0, uu - 2):uu + 3]) for uu, vv in zip(u, v)])
    br = L > T; best = (0, 0, 0); i = 0
    while i < len(br):
        if br[i]:
            j = i
            while j < len(br) and (br[j] or (j + 6 < len(br) and br[j:j + 6].any())): j += 1
            if j - i > best[0]: best = (j - i, i, j)
            i = j
        else: i += 1
    n, i0, i1 = best
    rows.append((b, f, rs[i0] if n else np.nan, rs[min(i1, len(rs) - 1)] if n else np.nan, n * 0.25))
for r in rows: print('%5.0f fence %5.1f  roof %6.1f .. %6.1f  (%4.1f m)' % r)
json.dump([[float(x) for x in r] for r in rows], open(os.path.join(SP, 'work', 'roofspan.json'), 'w'))
