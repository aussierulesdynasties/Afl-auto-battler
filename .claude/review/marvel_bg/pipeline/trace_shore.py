"""Director 2026-11-20 'Yes, trace + wall': trace the harbour shoreline from sat.png (reference only, used as a mask,
no pixels on the model). Water = dark pixels inside 40 m of the painted water, cleaned, holes (boats) filled.
Writes data/marvel/prep/shore.json (polygons in metres, x east y north) and a check image."""
import json, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
S = np.array(Image.open('data/marvel/sat.png').convert('RGB')).astype(np.float32)
N = S.shape[0]; MPP = 0.5; C = N / 2
g = np.array(Image.open('data/marvel/prep/ground.png').convert('RGB')).astype(int)
GW = np.abs(g - [52, 74, 84]).sum(2) < 12
# ground.png: 2000 px over 3000 m, top=north; sat: 2800 px over 1400 m, top=north
yy = ((np.arange(N) - C) * MPP + 1500) / 1.5   # sat row -> ground row (both north-up, centred)
gi = np.clip(yy.astype(int), 0, 1999)
GWs = GW[gi][:, gi]
near = nd.binary_dilation(GWs, iterations=30)                     # 15 m
lum = S.mean(2)
dark = lum < 70
M = near & (dark | (nd.uniform_filter(dark.astype(np.float32), 10) > 0.6))   # pile field (director: water only): mostly-dark 5 m patches are water
M = nd.binary_opening(M, iterations=3); M = nd.binary_closing(M, iterations=6)
M = nd.binary_fill_holes(M)
lab, k = nd.label(M); keep = np.zeros(k + 1, bool)
for i in np.unique(lab[GWs & M]): keep[i] = True
keep[0] = False
M = keep[lab]
sizes = nd.sum(M, lab, range(k + 1)); M &= (sizes[lab] > 4000)    # > 1000 m2
cs, _ = cv2.findContours(M.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
polys = []
for c in cs:
    c = cv2.approxPolyDP(c, 2.0, True)[:, 0, :]                   # 1 m tolerance
    if len(c) < 3: continue
    polys.append([[round((float(x) - C) * MPP, 2), round((C - float(y)) * MPP, 2)] for x, y in c])
json.dump({'polys': polys}, open('data/marvel/prep/shore.json', 'w'))
v = S.astype(np.uint8).copy(); cv2.drawContours(v, [np.array([[[ (p[0] / MPP + C), (C - p[1] / MPP)]] for p in P], np.int32) for P in polys], -1, (255, 0, 0), 3)
Image.fromarray(v).resize((1400, 1400)).save('out/marvel/shore_check.jpg', quality=85)
print('polys', len(polys), 'water m2', int(M.sum() * MPP * MPP))
# grid masks for scene.py (n x n, row j = south first, y = j*NS - NE): IN = traced water inside the sat square,
# BED = cells wholly under water (eroded 1 cell) where terrain drops; SAT = cells inside the sat square
meta = json.load(open('data/marvel/prep/meta.json')); NE, NS = meta['near'], meta['near_step']; n = int(round(2 * NE / NS)) + 1
c_ = np.arange(n) * NS - NE; X, Y = np.meshgrid(c_, c_)
SAT = (np.abs(X) < C * MPP - NS) & (np.abs(Y) < C * MPP - NS)
px = np.clip((C + X / MPP).astype(int), 0, N - 1); py = np.clip((C - Y / MPP).astype(int), 0, N - 1)
IN = M[py, px] & SAT
np.save('data/marvel/prep/shore_grid.npy', np.stack([IN, nd.binary_erosion(IN), SAT]))
print('grid water cells', int(IN.sum()), 'bed', int(nd.binary_erosion(IN).sum()))
# fine land mask (director 2026-11-20 'Yes, fine strip'): 1.5 m cells over the sat square, True = land; row = south first
FS_ = 1.5; m_ = int(C * MPP * 2 / FS_); fc = (np.arange(m_) + 0.5) * FS_ - C * MPP
FX, FY = np.meshgrid(fc, fc)
LAND = ~M[np.clip((C - FY / MPP).astype(int), 0, N - 1), np.clip((C + FX / MPP).astype(int), 0, N - 1)]
LAND = nd.binary_erosion(LAND, iterations=1, border_value=1)   # drop land squares touching water: the quay wall is the edge
np.save('data/marvel/prep/shore_fine.npy', LAND); print('fine', LAND.shape, 'origin', -C * MPP, 'step', FS_)
# exact land strip: water polygons buffered 18 m, minus the water, clipped to the sat square; constrained triangulation
import shapely
from shapely.geometry import Polygon as _P, box as _box
_wat = shapely.union_all([_P(p).buffer(0) for p in polys])
_strip = _wat.buffer(18.0).difference(_wat).intersection(_box(-C * MPP, -C * MPP, C * MPP, C * MPP))
_tris = [t for t in shapely.get_parts(shapely.constrained_delaunay_triangles(_strip))]
TV = np.array([np.array(t.exterior.coords)[:3] for t in _tris])
np.save('data/marvel/prep/shore_strip.npy', TV); print('strip tris', len(TV), 'area', int(_strip.area))
