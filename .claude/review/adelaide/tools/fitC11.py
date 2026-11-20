"""camera C: projection family test on towers + hotel points (plan -> model by planreg, photo px read off grid/C_hot_all.jpg)"""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from planreg import pl2m
from scipy.optimize import least_squares
def P(u, v): x, y = pl2m(u, v); return float(x), float(y)
def c2f(xc, yc): return 1420 + xc / 0.741, 820 + yc / 0.741
SE = (105.29, -75.82); NE = (65.65, 112.08)
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
pts = [(SE, zc, 490, 285), (NE, zc, 3425, 716),
       (P(1446, 1965), 20, *c2f(62, 35)), (P(1880, 2075), 20, *c2f(400, 40)), (P(1880, 2075), 3.6, *c2f(400, 355)),
       (P(1946, 1985), 21.6, *c2f(447, 30)), (P(2046, 1985), 21.6, *c2f(500, 30)), (P(2046, 1985), 0, *c2f(500, 415)),
       (P(2046, 1865), 18.1, *c2f(512, 68)), (P(2902, 1865), 18.1, *c2f(1035, 75)),
       (P(2046, 2107), 12, *c2f(520, 207)), (P(2902, 2107), 12, *c2f(1145, 225)), (P(2046, 2107), 7.2, *c2f(520, 300)),
       (P(2902, 1985), 21.6, *c2f(1040, 65)), (P(2985, 1985), 21.6, *c2f(1095, 65)),
       (P(3085, 2080), 20, *c2f(1185, 85)), (P(3497, 1990), 20, *c2f(1410, 100))]
X = np.array([[p[0][0], p[0][1], p[1]] for p in pts]); U = np.array([[p[2], p[3]] for p in pts])
def proj(q, X, M):
    x0, y0, yaw, f, cy, Z, ky = q
    d = X - [x0, y0, Z]; fx, fy = math.cos(yaw), math.sin(yaw); rx, ry = math.sin(yaw), -math.cos(yaw)
    dz = d[:, 0] * fx + d[:, 1] * fy; dx = d[:, 0] * rx + d[:, 1] * ry; rho = np.hypot(dx, dz); th = np.arctan2(dx, dz)
    h = d[:, 2]
    if M == 'rect': u = f * dx / dz; v = f * h / dz
    elif M == 'cyl': u = f * th; v = f * h / rho
    elif M == 'equi': u = f * th; v = f * np.arctan2(h, rho)
    elif M == 'merc': u = f * th; v = f * np.arcsinh(h / rho)
    elif M == 'stereo': u = 2 * f * np.tan(th / 2); v = f * h / rho
    return np.stack([1920 + u, cy - ky * v], 1)
for M in ('rect', 'cyl', 'equi', 'merc', 'stereo'):
    for kyfree in (False, True):
        res = lambda q: (proj(q if kyfree else np.r_[q[:6], 1.0], X, M) - U).ravel()
        best = None
        for x0 in (190, 220, 250, 280):
            for y0 in (-20, 0, 20):
                q0 = [x0, y0, math.radians(177.5), 2300, 1365, 1.6, 1.0]
                r = least_squares(res, q0, x_scale=[10, 10, 0.05, 200, 30, 1, 0.1])
                if best is None or r.cost < best.cost: best = r
        q = best.x; rr = res(q).reshape(-1, 2)
        print(M, 'ky' if kyfree else '  ', 'C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]),
              'eye', round(q[5], 1), 'ky', round(q[6], 3) if kyfree else 1, 'rms', round(float(np.sqrt(np.mean(rr ** 2))), 1),
              'max', int(np.abs(rr).max()))
        json.dump({'p': list(map(float, q[:5])), 'model': M, 'eye': float(q[5]), 'ky': float(q[6]) if kyfree else 1.0,
                   'res': np.round(rr).astype(int).tolist()}, open('grid/camC11_%s%s.json' % (M, '_ky' if kyfree else ''), 'w'))
