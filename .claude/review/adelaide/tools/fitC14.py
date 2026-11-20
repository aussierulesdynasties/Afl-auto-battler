"""camera C + the East Gate parts the plan can't pin (atrium glass line and top, pod front line and level), eye 1.6,
from hotel points + tower bearings"""
import numpy as np, math, json, sys
exec(open('tools/fitC11.py').read().split("for M in")[0])
from scipy.optimize import least_squares
AT = [8, 9]; POD = [10, 11, 12]
def geom(g):
    vA, zA, vP, dzP = g; Y = X.copy()
    for i, u in zip(AT, (2046, 2902)): Y[i, :2] = P(u, vA); Y[i, 2] = zA
    for i, u, z in zip(POD, (2046, 2902, 2046), (12, 12, 7.2)): Y[i, :2] = P(u, vP); Y[i, 2] = z + dzP
    return Y
out = {}
for M in ('rect', 'cyl'):
    def res(q):
        t = proj(np.r_[q[:5], 1.6, q[5]], geom(q[7:]), M); t[:, 1] += q[6] * (t[:, 0] - 1920) / 1000
        r = (t - U); return np.r_[r[:2, 0], r[2:].ravel()]
    best = None
    for x0 in (190, 220, 250, 280):
        for y0 in (-20, 0, 20):
            r = least_squares(res, [x0, y0, math.radians(177.5), 2300, 1365, 1.0, 0, 1865, 18.1, 2107, 0],
                              x_scale=[10, 10, 0.05, 200, 30, 0.1, 10, 20, 1, 20, 1])
            if best is None or r.cost < best.cost: best = r
    q = best.x; rr = res(q)
    print(M, 'C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4]), 'ky', round(q[5], 3),
          'roll', round(q[6], 1), 'atrium v', round(q[7]), 'top', round(q[8], 1), 'pod v', round(q[9]), 'dz', round(q[10], 2),
          'rms', round(float(np.sqrt(np.mean(rr ** 2))), 1))
    print('  ', np.round(rr).astype(int).tolist())
    json.dump({'p': list(map(float, q[:5])), 'model': M, 'eye': 1.6, 'ky': float(q[5]), 'roll': float(q[6]),
               'geom': list(map(float, q[7:]))}, open('grid/camC14_%s.json' % M, 'w'))
