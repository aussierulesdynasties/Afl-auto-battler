import os
# Where the 2012 roofs end beside the open north-east end: along arcs across the roof (front to back), the bearing
# where the white sheet ends (the min-channel drop), in the top-down shots, moved back for relief (z/H).
import cv2, json, math, numpy as np
from scipy.ndimage import gaussian_filter1d
C = json.load(open('cal.json')); S, DX, DY = C['s'], C['dx'], C['dy']; H = 3000.0
IMS = [(cv2.GaussianBlur(cv2.imread('ge/' + n + '.png').min(2).astype(np.float32), (0, 0), 0.8), sh) for n, sh in (('top3000', 0.0), ('topN', 60.0), ('topS', -60.0))]
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json')))
def per(t, q):
    t = np.array(t); return float(np.interp(q % 360, np.r_[t[:, 0] - 360, t[:, 0], t[:, 0] + 360], np.r_[t[:, 1], t[:, 1], t[:, 1]]))
def sample(e, n, z):
    # the image point of ground point (e, n) at height z: pushed out from each shot's nadir by z/H
    v = []
    for g, sh in IMS:
        cx, cy = DX, DY + sh; k = z / (H - z)
        ee, nn = e + (e - cx) * k, n + (n - cy) * k
        x = 640 + (ee - DX) / S; y = 360 - (nn - DY - sh) / S
        if 2 <= x < 1277 and 60 <= y < 717: v.append(cv2.getRectSubPix(g, (1, 1), (float(x), float(y)))[0, 0])
    return np.mean(v) if v else np.nan
res = {}
for nm, (lo, hi), zf, zb in (('E', (66, 84), 18.2, 18.0), ('N', (358, 376), 18.0, 18.0)):
    rows = []
    for f in np.linspace(0.08, 0.92, 8):
        bs = np.arange(lo, hi, 0.05)
        L = np.array([sample(*(lambda r: (r * math.sin(math.radians(b)), r * math.cos(math.radians(b))))(per(D['rf'], b) + (per(D['rb'], b) - per(D['rf'], b)) * f), zf + (zb - zf) * f) for b in bs])
        L = gaussian_filter1d(L, 3); g = np.gradient(L)
        # E: the sheet lies at larger bearings (white rises going clockwise); N: at smaller (white falls)
        k = int(np.argmax(g if nm == 'E' else -g)); b = bs[k]; r = per(D['rf'], b) + (per(D['rb'], b) - per(D['rf'], b)) * f
        rows.append((round(float(f), 2), round(float(b % 360), 2), round(r, 1), round(float(abs(g[k]) * 20), 1)))
    res[nm] = rows
    print(nm, rows)
json.dump(res, open('roofends.json', 'w'))
# a straight end (square in plan) through the strong edges (gradient over 90): the bearing at the front and back
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'engie.json'); D = json.load(open(P))
for nm, key in (('E', 'b0'), ('N', 'b1')):
    a = np.array([(f, b) for f, b, r, g in res[nm] if g > 90]); b_ = np.where(a[:, 1] < 180, a[:, 1] + (360 if nm == 'N' else 0), a[:, 1])
    k, c = np.polyfit(a[:, 0], b_, 1); rms = np.sqrt(np.mean((np.polyval([k, c], a[:, 0]) - b_) ** 2))
    print('%s roof %s end: %.2f deg at the front, %.2f at the back (rms %.2f deg over %d arcs)' % (nm, key, c, c + k, rms, len(a)))
    for st in D['stands']:
        if st['name'] == nm: st['roof_ends'] = {key: [round(float(c), 2), round(float(c + k), 2)]}
json.dump(D, open(P, 'w'), indent=1)
