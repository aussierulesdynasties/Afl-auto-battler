"""What stands on the flat roofs: air-conditioning units, plant rooms, vents and skylight housings, read from the close
straight-down aerial (aerial19.py) as car-to-room-sized patches that differ from the roof around them. Positions,
sizes and colours only: no aerial pixels go into the scene. Flat roofs are prep's buildings that scene.py draws with a
parapet (real place, class block, not a shed, not an open canopy), 250 m2 and over, within 1.3 km.
usage (after prep.py): roofplant.py spec.json -> data/<g>/roofplant.json  [[building index, x, y, length, width,
heading rad, height, r, g, b], ...]"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
spec = json.load(open(sys.argv[1])); name = spec['name']
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, 'data', name)
import aerial19 as _a19
_a19.setup(spec, D); from aerial19 import aerial, S
BL = json.load(open(os.path.join(D, 'prep', 'buildings.json')))
def area(A): return 0.5 * np.sum(A[:, 0] * np.roll(A[:, 1], -1) - A[:, 1] * np.roll(A[:, 0], -1))
out = []; nb = 0
for bi, b in enumerate(BL):
    if b.get('c') != 'block' or b.get('open') or (b.get('shed') and b['h'] <= 14): continue
    A = np.array(b['p'], float)
    if abs(area(A)) < 250 or np.hypot(*A.mean(0)) > 1300: continue
    x0, y0 = A.min(0) - 1; x1, y1 = A.max(0) + 1
    if (x1 - x0) * (y1 - y0) > 60000: continue
    img, xs, ys = aerial(x0, y0, x1, y1); h, w = img.shape[:2]
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).polygon([((x - x0) / S, (y1 - y) / S) for x, y in A], fill=1)
    ok = ndi.binary_erosion(np.asarray(mk) > 0, iterations=6)          # 1.5 m in from the parapet (its shadow, the lean of a tall wall)
    if ok.sum() < 300: continue
    nb += 1
    med = np.median(img[ok], 0); lum = img.mean(-1); ml = med.mean()
    dist = np.abs(img - med).max(-1)
    # a unit: a patch 1-8 m across clearly off the roof's colour (bright metal housings, dark plant rooms); a dark patch
    # beside a bright one is that unit's shadow
    lite = ok & (dist > 30) & (lum > ml - 10); dark = ok & (lum < ml - 35)
    lite = ndi.binary_opening(lite, np.ones((3, 3), bool)); dark = ndi.binary_opening(dark, np.ones((3, 3), bool))
    def blobs(m):
        lab, n = ndi.label(m)
        for i, sl in enumerate(ndi.find_objects(lab)):
            jj, ii = np.nonzero(lab[sl] == i + 1); a = len(jj) * S * S
            if a < 1.2 or a > 70: continue
            X = xs[ii + sl[1].start]; Y = ys[jj + sl[0].start]
            c = np.array([X.mean(), Y.mean()]); q = np.stack([X - c[0], Y - c[1]], 1)
            ev, evec = np.linalg.eigh(np.cov(q.T) + 1e-6 * np.eye(2))
            L = max(1.0, math.sqrt(12 * ev[1])); W = max(0.8, math.sqrt(12 * ev[0]))   # extent of a uniform rectangle
            if L > 10 or L * W > 1.8 * a + 2: continue                      # long thin lines (gutters, joints, seams): not units
            yield c, L, W, math.atan2(evec[1, 1], evec[0, 1]), np.median(img[jj + sl[0].start, ii + sl[1].start], 0), a
    lb = list(blobs(lite)); db = [d for d in blobs(dark) if all(np.hypot(*(d[0] - q[0])) > 0.6 * (q[1] + d[1]) for q in lb)]
    for (c, L, W, hd, col, a), dk in [(q, 0) for q in lb] + [(q, 1) for q in db]:
        ht = 1.0 + 0.9 * min(1.0, a / 30.0) if not dk else 1.6 + 1.0 * min(1.0, a / 40.0)   # housings low, plant rooms taller
        out.append([bi, round(float(c[0]), 2), round(float(c[1]), 2), round(L, 2), round(W, 2), round(hd, 3), round(ht, 2), *[int(v) for v in col]])
json.dump(out, open(os.path.join(D, 'roofplant.json'), 'w'))
print('ROOFPLANT roofs', nb, 'units', len(out))
