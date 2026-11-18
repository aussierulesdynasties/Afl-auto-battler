"""Photo B camera from hand-picked points (pixel -> world metres)."""
import numpy as np, json, math, os, sys
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def R(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
def proj(p, X):
    X = np.atleast_2d(X); d = (X - p[:3]) @ R(*p[3:6]).T
    return np.stack([p[7] + p[6] * d[:, 0] / d[:, 2], p[8] - p[6] * d[:, 1] / d[:, 2]], 1)
W, H = 1950, 1301
PTS = json.load(open(os.path.join(ROOT, 'ptsB.json')))
X = np.array([q[1] for q in PTS]); U = np.array([q[0] for q in PTS], float)
def res(q):
    p = np.r_[q, W / 2, H / 2]; return (proj(p, X) - U).ravel()
best = None
if os.path.exists(os.path.join(ROOT, 'camB.json')) and '--grid' not in sys.argv:
    best = least_squares(res, np.array(json.load(open(os.path.join(ROOT, 'camB.json')))['p'][:7]), method='lm', max_nfev=5000)
else:
  for az in range(150, 240, 15):
    for el in (20, 30, 40, 50):
        for dist in (300, 450, 650):
            T = np.array([-40.0, -60.0, 0.0]); a, e = math.radians(az), math.radians(el)
            C = T + dist * np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
            f = (T - C) / np.linalg.norm(T - C)
            for fo in (1200, 2000, 3000):
                q0 = np.r_[C, math.atan2(f[1], f[0]), math.asin(f[2]), 0.0, fo]
                try: r = least_squares(res, q0, method='lm', max_nfev=3000)
                except Exception: continue
                if best is None or r.cost < best.cost: best = r
p = np.r_[best.x, W / 2, H / 2]
e = np.linalg.norm((proj(p, X) - U), axis=1)
for q, ee in zip(PTS, e): print(q[2], round(ee, 1))
print('rms', round(float(np.sqrt((e ** 2).mean())), 2), 'C', np.round(p[:3]), 'yaw', round(math.degrees(p[3])), 'pitch', round(math.degrees(p[4]), 1), 'f', round(p[6]))
json.dump({'p': list(p), 'W': W, 'Himg': H}, open(os.path.join(ROOT, 'camB.json'), 'w'))
