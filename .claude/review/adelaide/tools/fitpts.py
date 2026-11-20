"""fitpts.py PTS.json OUT_CAM.json : pinhole camera fit to labelled points (world xyz <-> photo px) plus optional
curves (world polyline <-> photo points, distance to the projected curve). p = [Cx,Cy,Cz,yaw,pitch,roll,f,cx,cy]"""
import sys, json, math, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, 'tools'); from fitcam import proj
J = json.load(open(sys.argv[1])); W, H = J['W'], J['H']
X = np.array([p[0] for p in J['pts']], float); U = np.array([p[1] for p in J['pts']], float)
CV = [(np.array(c[0], float), np.array(c[1], float), c[2] if len(c) > 2 else 1.0) for c in J.get('curves', [])]
def dens(P, st=0.5):
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(np.linalg.norm(b - a) / st)); out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(out)
CV = [(dens(c), q, w) for c, q, w in CV]
fix = J.get('fix', {})
def full(q):
    p = list(q[:7]) + [W / 2, H / 2]
    for k, v in fix.items(): p[int(k)] = v
    return np.array(p)
def res(q):
    p = full(q); r = list((proj(p, X) - U).ravel())
    for c, pts, w in CV:
        pp = proj(p, c); r += list(w * np.sqrt(((pts[:, None] - pp[None]) ** 2).sum(-1)).min(1))
    return np.array(r)
best = None
for C0 in J['C0']:
    for yaw in np.radians(np.arange(0, 360, 20)):
        q0 = list(C0) + [yaw, -0.1, 0.0, J.get('f0', W)]
        try: s = least_squares(res, q0, bounds=(J.get('lo', [-1e4, -1e4, 0, -20, -1.5, -0.3, 100]), J.get('hi', [1e4, 1e4, 500, 20, 1.0, 0.3, 50000])))
        except Exception: continue
        rms = math.sqrt((s.fun ** 2).mean())
        if best is None or rms < best[0]: best = (rms, s.x)
p = full(best[1]); print('rms px', round(best[0], 2), [round(v, 3) for v in p])
print('resid', np.round(proj(p, X) - U, 1).tolist())
json.dump({'p': list(map(float, p)), 'W': W, 'Himg': H}, open(sys.argv[2], 'w'))
