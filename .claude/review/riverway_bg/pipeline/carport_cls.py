# Classify carport groups by eye from aerial contact sheets (out/riverway/chk/sailgroups_*.png), 2026-11-20.
# 1 = shade sail (sand fabric, Street View Sept 2022), 2 = solar-panel carport row, 3 = arched dark canopy, 0 = not a carport (roof/car/tree)
import json, numpy as np
from scipy import ndimage as nd
SAIL = {1, 2, 3}
SOLAR = {5, 6, 7, 8, 9, 10, 11, 13, 17, 18, 21, 22, 24, 26, 27, 34}
ARCH = {4, 23, 28, 29, 30, 36, 37, 40, 53}
P = 'data/riverway/prep/'
C = np.array(json.load(open(P + 'carports.json')), float)
ij = C[:, :2].astype(int); x0, y0 = ij.min(0)
g = np.zeros(tuple(ij.max(0) - ij.min(0) + 1), bool); g[ij[:, 0] - x0, ij[:, 1] - y0] = 1
L, n = nd.label(g); a = nd.sum(g, L, range(1, n + 1))
order = [i + 1 for i in np.argsort(-a) if a[i] >= 60]          # label ids ranked: #1 .. #59
rank = {lab: k + 1 for k, lab in enumerate(order)}
lab = L[ij[:, 0] - x0, ij[:, 1] - y0]
cls = np.array([1 if rank.get(l) in SAIL else 2 if rank.get(l) in SOLAR else 3 if rank.get(l) in ARCH else 0 for l in lab])
grp = np.array([rank.get(l, 0) for l in lab])
out = [[*c, int(k), int(r)] for c, k, r in zip(C.tolist(), cls, grp) if k]
json.dump(out, open(P + 'carports_cls.json', 'w'))
for k, nm in [(1, 'sail'), (2, 'solar'), (3, 'arched'), (0, 'dropped')]: print(nm, int((cls == k).sum()), 'm2')
