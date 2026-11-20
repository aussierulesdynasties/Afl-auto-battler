"""camera C (cylindrical panorama) refit on more anchors: towers, gate-box corners, roof valleys, lawn tip.
Esri roof pixels are lean-corrected to ground: x - 0.82*h, y - 0.26*h. bearings in a cyl pano don't depend on height."""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from projC import R
from esri import px2m
from scipy.optimize import least_squares
Z = float(os.environ.get('EYE', '1.6'))
def g(px, py, h): return px2m(px - 0.82 * h, py - 0.26 * h)
SE = np.array([105.29, -75.82]); NE = np.array([65.65, 112.08])
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
GL, GR = [float(v) for v in os.environ.get('GATE', '2110,2820').split(',')]
pts = [  # (plan xy, z, photo x, photo y or None, weight)
    (SE, zc, 490, 285, 1), (NE, zc, 3425, 716, 1),
    (g(1311, 1311, 30), 0, 1150, None, 1), (g(1327, 1171, 30), 0, 1940, None, 1), (g(1289.5, 996, 30), 0, 2750, None, 1),
    (px2m(1461, 1137), 0, 2355, 1425, 0.5 if not os.environ.get('NOLAWN') else 0)]
def proj(q, X):
    d = (np.array(X, float) - [q[0], q[1], Z]) @ R(q[2], 0, 0).T
    rho = np.hypot(d[:, 0], d[:, 2])
    return np.stack([1920 + q[3] * np.arctan2(d[:, 0], d[:, 2]), q[4] - q[3] * d[:, 1] / rho], 1)
X = [[p[0][0], p[0][1], p[1]] for p in pts]
def res(q):
    t = proj(q, X); r = []
    for (P, z, u, v, w), tt in zip(pts, t):
        r.append(w * (tt[0] - u))
        if v is not None: r.append(w * (tt[1] - v))
    r.append((q[4] - 1360) * 0.3)
    return np.array(r)
best = None
for x0 in (180, 210, 250):
    for y0 in (-40, -20, 0):
        r = least_squares(res, [x0, y0, math.pi, 2000, 1360])
        if best is None or r.cost < best.cost: best = r
q = best.x; t = proj(q, X)
print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]))
for (P, z, u, v, w), tt in zip(pts, t): print(' photo', u, v, '-> model', np.round(tt))
if os.environ.get('WRITE'): json.dump({'p': list(map(float, q)), 'model': 'cyl', 'eye': Z}, open('camC5.json', 'w'))
