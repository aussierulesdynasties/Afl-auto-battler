"""camera C, generalised projection: x = cx + f*tan(k*th)/k, y = cy - f*h/(rho*cos(k*th)); k=0 cylindrical, k=1 rectilinear.
anchors: tower shafts + collars, roof valleys (Esri, lean-corrected), lawn tip; optional hotel floor scale."""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from projC import R
from esri import px2m
from scipy.optimize import least_squares
Z = float(os.environ.get('EYE', '1.6'))
def g(px, py, h): return px2m(px - 0.82 * h, py - 0.26 * h)
SE = np.array([105.29, -75.82]); NE = np.array([65.65, 112.08])
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
pts = [(SE, zc, 490, 285, 1), (NE, zc, 3425, 716, 1),
    (g(1311, 1311, 30), 0, 1150, None, 1), (g(1327, 1171, 30), 0, 1940, None, 1), (g(1289.5, 996, 30), 0, 2750, None, 1),
    (px2m(1461, 1137), 0, 2355, 1425, float(os.environ.get('WL', '0.5')))]
X = np.array([[p[0][0], p[0][1], p[1]] for p in pts])
def proj(q, X):
    k = q[5] if len(q) > 5 else 0.0
    d = (np.array(X, float) - [q[0], q[1], Z]) @ R(q[2], 0, 0).T
    rho = np.hypot(d[:, 0], d[:, 2]); th = np.arctan2(d[:, 0], d[:, 2])
    xs = th if abs(k) < 1e-6 else np.tan(k * th) / k
    return np.stack([1920 + q[3] * xs, q[4] - q[3] * d[:, 1] / (rho * np.cos(k * th))], 1)
KFIX = os.environ.get('K')
def res(q):
    if KFIX is not None: q = np.r_[q, float(KFIX)]
    t = proj(q, X); r = []
    for (P, z, u, v, w), tt in zip(pts, t):
        r.append(w * (tt[0] - u))
        if v is not None: r.append(w * (tt[1] - v))
    r.append((q[4] - 1360) * 0.3)
    return np.array(r)
best = None
for x0 in (180, 210, 250):
    for y0 in (-30, -10, 10):
        for k0 in ((0.0, 0.5, 0.9) if KFIX is None else (None,)):
            q0 = [x0, y0, math.pi, 2000, 1360] + ([k0] if KFIX is None else [])
            r = least_squares(res, q0)
            if best is None or r.cost < best.cost: best = r
q = best.x if KFIX is None else np.r_[best.x, float(KFIX)]; t = proj(q, X)
print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]), 'k', round(q[5], 3), 'rms', round(np.sqrt(np.mean(best.fun[:-1] ** 2)), 1))
for (P, z, u, v, w), tt in zip(pts, t): print(' photo', u, v, '-> model', np.round(tt))
# hotel floor check: left copper wing face (Esri roof 1453,1185 lean 20 m) floors 86 px apart at photo x~1600
H = g(1453, 1185, 20); tt = proj(q, [[H[0], H[1], 10], [H[0], H[1], 13.3]]); print(' 3.3 m floor at the left wing =', round(tt[0, 1] - tt[1, 1]), 'px (photo ~86) at x', round(tt[0, 0]))
if os.environ.get('WRITE'): json.dump({'p': list(map(float, q[:5])), 'k': float(q[5]), 'model': 'gen', 'eye': Z}, open('camC6.json', 'w'))
