"""camera C fit on hard points: towers + hotel corners from the COX lodged plans (planreg) at their RL heights.
Eye height free. The lawn drape is only reported, not fitted."""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from esri import px2m
from planreg import pl2m
from scipy.optimize import least_squares
def g(px, py, h): return px2m(px - 0.82 * h, py - 0.26 * h)
def P(u, v): x, y = pl2m(u, v); return float(x), float(y)
SE = (105.29, -75.82); NE = (65.65, 112.08)
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
# (model xy, z, photo u, photo v or None)
pts = [(SE, zc, 490, 285), (NE, zc, 3425, 716),
       
       (P(1446, 1965), 20, 1503, 870),   # south copper block, left silhouette, roof
       (P(1880, 2080), 20, 1964, 870),   # south block, north end of east face, roof
       (P(1880, 2080), 3.6, 1964, 1300), # same, L2 slab
       (P(2046, 2107), 12, 2111, 1098),  # pod, south top corner
       (P(2902, 2107), 12, 2967, 1120),  # pod, north top corner
       (P(3085, 2080), 20, 3019, 937),   # north block, south end, roof
       (P(3497, 1990), 20, 3321, 945)]   # north block, right silhouette, roof
X = np.array([[p[0][0], p[0][1], p[1]] for p in pts])
def proj(q, X):
    x0, y0, yaw, f, cy, Z = q[:6]
    d = X - [x0, y0, Z]; fx, fy = math.cos(yaw), math.sin(yaw); rx, ry = math.sin(yaw), -math.cos(yaw)
    dz = d[:, 0] * fx + d[:, 1] * fy; dx = d[:, 0] * rx + d[:, 1] * ry; rho = np.hypot(dx, dz)
    if os.environ.get('MODEL') == 'rect':
        return np.stack([1920 + f * dx / dz, cy - f * d[:, 2] / dz], 1)
    if os.environ.get('MODEL') == 'roll':
        u = 1920 + f * np.arctan2(dx, dz); return np.stack([u, cy - f * d[:, 2] / rho + q[6] * (u - 1920) / 1000], 1)
    return np.stack([1920 + f * np.arctan2(dx, dz), cy - f * d[:, 2] / rho], 1)
def res(q):
    t = proj(q, X); r = []
    for p, tt in zip(pts, t):
        r.append(tt[0] - p[2])
        if p[3] is not None: r.append(tt[1] - p[3])
    return np.array(r)
best = None
for x0 in (200, 220, 240, 260, 280):
    for y0 in (-30, -10, 10):
        q0 = [x0, y0, math.radians(177.5), 2300, 1365, 1.6] + ([0] if os.environ.get('MODEL')=='roll' else [])
        r = least_squares(res, q0, x_scale=[10, 10, 0.05, 200, 30, 1] + ([10] if os.environ.get('MODEL')=='roll' else []))
        if best is None or r.cost < best.cost: best = r
q = best.x; rr = res(q)
print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]), 'eye', round(q[5], 2),
      'rms', round(float(np.sqrt(np.mean(rr ** 2))), 1))
print('res', np.round(rr).astype(int).tolist())
print('hotel model xy', [tuple(np.round(p[0], 1)) for p in pts[5:]])
json.dump({'p': list(map(float, q[:5])), 'model': 'cyl', 'eye': float(q[5])}, open('camC10b.json', 'w'))
