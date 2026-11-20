"""camera C as a CYLINDRICAL panorama (verticals corrected): x = cx + f*atan(dx/dz), y = cy - f*h/rho.
eye 1.6 m. fit x,y,yaw,f,cy on tower bearings + lawn tip; collars (+frames if FULL) checked. writes camC4.json"""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from projC import R
from esri import px2m
from scipy.optimize import least_squares
Z = 1.6; lawn = px2m(1461, 1137)
SE = np.array([105.29, -75.82]); NE = np.array([65.65, 112.08])
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
def proj(q, X):
    d = (np.array(X, float) - [q[0], q[1], Z]) @ R(q[2], 0, 0).T
    rho = np.hypot(d[:, 0], d[:, 2])
    return np.stack([1920 + q[3] * np.arctan2(d[:, 0], d[:, 2]), q[4] - q[3] * d[:, 1] / rho], 1)
FULL = os.environ.get('FULL')
def res(q):
    t = proj(q, [[*SE, zc], [*NE, zc], [lawn[0], lawn[1], 0]])
    r = [t[0, 0] - 490, t[1, 0] - 3425, t[2, 0] - 2355, t[2, 1] - 1425, (q[4] - 1360) * 0.3]
    if FULL: r += [t[0, 1] - 285, t[1, 1] - 716]
    return np.array(r)
best = None
for x0 in (170, 200, 240):
    for y0 in (-20, 0, 20):
        r = least_squares(res, [x0, y0, math.pi, 1400, 1360])
        if best is None or r.cost < best.cost: best = r
q = best.x
print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]), 'res', np.round(best.fun, 1))
print('collars (photo 285, 716):', np.round(proj(q, [[*SE, zc], [*NE, zc]])[:, 1]))
json.dump({'p': list(map(float, q)), 'model': 'cyl'}, open('camC4.json', 'w'))
