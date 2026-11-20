import numpy as np, math, sys, json
sys.path.insert(0, 'fit'); from cam import *
from scipy.optimize import least_squares
exec(open('fit/fit_g18.py').read().split('W, H =')[0].split('from scipy.optimize import least_squares')[1])
W, H = 1400, 1031
def full(x2, y2): return (x2 / 2 + 480, y2 / 2 + 380)
BASE = [(45,512),(213,512),(381,512),(545,508),(708,505),(940,497),(1097,495),(1250,493),(1393,490)]
LOWE = [(45,318),(213,300),(381,290),(545,282),(708,275)]
LOWP = [(130,232),(300,222),(465,212),(635,198)]
TALLV = [(940,185),(1097,165),(1250,145),(1393,111)]
TALLP = [(1015,75),(1160,52),(1320,28)]
def res(q):
    ex, ey, yaw, pit, rol, f, zb0, hl, rl, ht, rt, wl, w4, wt = q
    ez = 1.6
    p = [ex, ey, ez, yaw, pit, rol, f]; r = []
    S = [0.0]
    for k in range(9): S.append(S[-1] + (wl if k < 4 else (w4 if k == 4 else wt)))
    M_ = lambda k: (S[k] + S[k + 1]) / 2
    def add(pts3, pts2):
        pr = proj(p, np.array(pts3, float), W / 2, H / 2)
        for a, b in zip(pr, pts2): r.extend(a - np.array(full(*b)))
    add([(*at(S[k]), zb0) for k in range(9)], BASE)
    add([(*at(S[k]), hl) for k in range(5)], LOWE)
    add([(*at(M_(k)), hl + rl) for k in range(4)], LOWP)
    add([(*at(S[k]), ht) for k in range(5, 9)], TALLV)
    add([(*at(M_(k)), ht + rt) for k in range(5, 8)], TALLP)
    far = np.array([[ex + 1e5 * math.cos(yaw), ey + 1e5 * math.sin(yaw), ez]])
    r.append((proj(p, far, W / 2, H / 2)[0, 1] - 577.0) * 3)
    return np.array(r)
best = None
for ex, ey in ((-30, -50), (-40, -30), (-20, -60), (-60, -10), (0, -40), (-10, -20)):
    for f in (1400, 2800):
        q0 = [ex, ey, math.atan2(-98 - ey, 10 - ex), 0.0, 0.0, f, 0.6, 5.3, 2.0, 7.5, 2.5, 5.2, 5.2, 5.2]
        try: r = least_squares(res, q0)
        except Exception: continue
        if best is None or r.cost < best.cost: best = r
q = best.x
print('cost', round(best.cost, 1), 'rms', round(math.sqrt(2 * best.cost / len(best.fun)), 1))
print('eye', np.round(q[:2], 2), 'yaw', round(math.degrees(q[2]), 2), 'pitch', round(math.degrees(q[3]), 2), 'roll', round(math.degrees(q[4]), 2), 'f', round(q[5]))
print('zbase', round(q[6], 2), 'low eave', round(q[7], 2), 'low rise', round(q[8], 2), 'tall eave', round(q[9], 2), 'tall rise', round(q[10], 2), 'widths', np.round(q[11:], 2))
print(np.round(best.fun, 1).tolist())
json.dump({'p': [q[0], q[1], 1.6] + list(q[2:6]), 'W': W, 'H': H, 'h': list(q[6:])}, open('fit/cam_g18.json', 'w'))
