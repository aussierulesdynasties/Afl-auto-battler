"""Solar-shade canopies over the stadium's east car park, measured from the aerial (reference only): panel pixels are dark
blue-grey (b > r, max < 0.40). Each canopy block -> its minimum-area rectangle. -> data/cazalys/prep/solar.json [[cx, cy, len, wid, ang_deg]]"""
import json, math, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure as ms
H, M = 1600, 0.6
A = np.asarray(Image.open('data/cazalys/sat.png').convert('RGB'), np.float32) / 255
c0, c1 = int((40 + H) / M), int((175 + H) / M); r0, r1 = int((H + 15) / M), int((H + 150) / M)
S = A[r0:r1, c0:c1]; r, g, b = S[..., 0], S[..., 1], S[..., 2]
m = (b > r + 0.025) & (S.max(2) < 0.40) & (S.max(2) > 0.08)
m = ndi.binary_opening(ndi.binary_closing(m, iterations=1), iterations=2)
Image.fromarray((m * 255).astype(np.uint8)).resize((m.shape[1] * 4, m.shape[0] * 4)).save("../dbg_solar.png")
lab, n = ndi.label(m); out = []
for i in range(1, n + 1):
    yy, xx = np.nonzero(lab == i)
    if len(yy) * M * M < 60: continue
    X = -H + (c0 + xx + 0.5) * M; Y = H - (r0 + yy + 0.5) * M; P = np.stack([X, Y], 1)
    best = None
    for a in np.radians(np.arange(0, 180, 1.0)):
        u = P @ [math.cos(a), math.sin(a)]; v = P @ [-math.sin(a), math.cos(a)]
        ar = (np.ptp(u) + M) * (np.ptp(v) + M)
        if best is None or ar < best[0]: best = (ar, a, u, v)
    ar, a, u, v = best; cu, cv = (u.max() + u.min()) / 2, (v.max() + v.min()) / 2
    L, W = np.ptp(u) + M, np.ptp(v) + M
    fill = len(yy) * M * M / ar
    if fill < 0.55: continue
    if W > L: L, W, a = W, L, a + math.pi / 2; 
    cx = cu * math.cos(best[1]) - cv * math.sin(best[1]); cy = cu * math.sin(best[1]) + cv * math.cos(best[1])
    out.append([round(cx, 2), round(cy, 2), round(L, 1), round(W, 1), round(math.degrees(a) % 180, 1), round(fill, 2)])
json.dump(out, open('data/cazalys/prep/solar.json', 'w'))
for o in sorted(out): print(o)
print(len(out), 'canopies', round(sum(o[2] * o[3] for o in out)), 'm2')
