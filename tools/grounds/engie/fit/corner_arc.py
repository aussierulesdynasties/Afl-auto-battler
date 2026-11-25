# The east roof's front edge is two arcs, not one: the long arc (tangent to the 1998 bowl in the tower gap) and,
# towards the open end, a tighter one that flares the edge outward (cornerE.py's points), tangent to the first.
# Fits both together over 72 to 133 deg and writes them into arcs.json (rf_E, with 'corner').
import os, json, math, numpy as np
from scipy.optimize import least_squares
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'composite.py')).read().split('OUT={}')[0])
A = json.load(open('arcs.json'))
b, P = pts('rf'); m = inr(b, 72.0, 133.0); Q = P[m]; QB = b[m]
def tcirc(bj, R):
    t = tparam_at_bearing(bj, dF); P0, tg = offset_pt(np.array([t]), dF); n = np.array([tg[0][1], -tg[0][0]])
    return P0[0] + R * n, R
def hit(c, R, bb):
    u = np.array([math.sin(math.radians(bb)), math.cos(math.radians(bb))]); uc = u @ c
    return uc + math.sqrt(max(uc * uc - (c @ c - R * R), 0.0))
def model(y):
    bj, R, bk, R2 = y; c, _ = tcirc(bj, R)
    Pk = np.array([math.sin(math.radians(bk)), math.cos(math.radians(bk))]) * hit(c, R, bk)
    c2 = Pk + (c - Pk) / np.linalg.norm(c - Pk) * R2
    return c, R, bk, c2, R2
def radius(y, bb):
    c, R, bk, c2, R2 = model(y)
    return np.array([hit(c2, R2, x) if x < bk else hit(c, R, x) for x in bb])
def res(y):
    r = np.hypot(Q[:, 0], Q[:, 1]) - radius(y, QB); return np.clip(r, -4, 4)
best = None
for bk0 in (80, 90, 100, 110, 120):
    for R20 in (50, 150, 400):
        try:
            z = least_squares(res, [A['rf_E']['bj'], A['rf_E']['R'], bk0, R20], bounds=([134, 40, 76, 10], [143, 3000, 128, 3000]))
        except Exception:
            continue
        if best is None or z.cost < best.cost: best = z
y = best.x; r = np.hypot(Q[:, 0], Q[:, 1]) - radius(y, QB); k = np.abs(r) < 4
c, R, bk, c2, R2 = model(y)
print('east roof front: long arc tangent at %.1f deg R=%.0f, corner arc from %.1f deg R=%.0f: rms %.2f 95%% %.2f max %.2f (n %d, %d mistraces >4 m)'
      % (y[0], R, bk, R2, np.sqrt((r[k] ** 2).mean()), np.percentile(np.abs(r[k]), 95), np.abs(r[k]).max(), k.sum(), (~k).sum()))
for lo, hi in ((72, 88), (88, 133)):
    mm = k & (QB >= lo) & (QB < hi); print('   %d-%d deg: rms %.2f (n %d)' % (lo, hi, np.sqrt((r[mm] ** 2).mean()), mm.sum()))
A['rf_E'].update({'bj': float(y[0]), 'c': c.tolist(), 'R': float(R), 'corner': {'bk': float(bk), 'c': c2.tolist(), 'R': float(R2)}})
json.dump(A, open('arcs.json', 'w'))
