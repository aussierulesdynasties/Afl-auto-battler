"""camera C, verticals corrected (pitch=roll=0), eye 1.6 m, horizon cy from the statue (1360).
unknowns x,y,yaw,f from tower shaft bearings + lawn tip (x,y). tower collars are a check only. writes camC3.json"""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from projC import R
from esri import px2m
from scipy.optimize import least_squares
CY = float(os.environ.get('CY', 1360)); Z = 1.6
lawn = px2m(1461, 1137)
SE = np.array([105.29, -75.82]); NE = np.array([65.65, 112.08])
def proj(q, X):
    p = [q[0], q[1], Z]; d = (np.array(X, float) - p) @ R(q[2], 0, 0).T
    return np.stack([1920 + q[3] * d[:, 0] / d[:, 2], CY - q[3] * d[:, 1] / d[:, 2]], 1)
def res(q):
    t = proj(q, [[*SE, 50], [*NE, 50], [lawn[0], lawn[1], 0]])
    return np.r_[t[0, 0] - 490, t[1, 0] - 3425, t[2, 0] - 2355, t[2, 1] - 1425]
best = None
for x0 in (170, 190, 210, 230):
    for y0 in (-10, 5, 20):
        r = least_squares(res, [x0, y0, math.pi, 1500])
        if best is None or r.cost < best.cost: best = r
q = best.x
print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'res', np.round(best.fun, 2))
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
print('collar check (photo SE y285, NE y716):', np.round(proj(q, [[*SE, zc], [*NE, zc]])[:, 1], 0))
json.dump({'p': [q[0], q[1], Z, q[2], 0.0, 0.0, q[3], 1920.0, CY], 'W': 3840, 'Himg': 2160}, open('camC3.json', 'w'))
