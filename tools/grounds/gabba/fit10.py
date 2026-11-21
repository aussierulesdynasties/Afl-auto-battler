# g49 camera fit with the satellite plan held fixed (model_in6.json): roof inner + outer edges, seat front, tower bases.
import numpy as np, json, math
from scipy.optimize import least_squares
exec(open('cam.py').read())
D = json.load(open('model_in6.json')); E = json.load(open('edges.json'))
cxm, cym = D['Cc']; B = D['booms']; zi, zo = D['zi'], D['zo']; SC, AR = 2.0, 2.5
ip = lambda a, k: float(np.interp((a + math.pi) % (2 * math.pi) - math.pi, D[k][0], D[k][1], period=2 * math.pi))
inner, outer = [], []
for i in range(len(B)):
    a0 = B[i]; a1 = B[(i + 1) % len(B)] + (2 * math.pi if B[(i + 1) % len(B)] < a0 else 0)
    for t in np.linspace(0, 1, 16, endpoint=False):
        a = a0 + (a1 - a0) * t
        r = ip(a, 'RI') + SC * 4 * t * (1 - t); inner.append((cxm + r * math.cos(a), cym + r * math.sin(a), zi))
        r = ip(a, 'RO'); outer.append((cxm + r * math.cos(a), cym + r * math.sin(a), zo - AR * math.sin(math.pi * t)))
inner, outer = np.array(inner), np.array(outer)
seat = np.array([(cxm + ip(a, 'pitch') * math.cos(a), cym + ip(a, 'pitch') * math.sin(a)) for a in np.linspace(-math.pi, math.pi, 720, endpoint=False)])
cx0, cy0 = 820, 600
ang = lambda p: math.degrees(math.atan2(p[1] - cy0, p[0] - cx0))
pin = np.array([p for p in E['inner'] if not (-65 < ang(p) < 20)], float)
pout = np.array(E['outer'], float)
BL = np.array([(480,730),(480,680),(480,630),(489,586),(511,546),(555,505),(599,483),(612,467),(705,436),(780,422),(880,425),(950,430),
 (1047,453),(1106,494),(1133,533),(1150,578),(1157,633),(1147,678),(1128,717),(1094,747),(1050,778)], float)
TWR = D['towers']   # SE SW NE NW
TP = [((377,163),(398,370),None),((1112,108),(1081,297),None),((433,697),(457,975),(459,983)),((1455,632),(1362,875),(1358,885))]
TW = [((-82.0,65.0),(1354,590)),((-110.4,64.3),(1470,555)),((-111.5,103.2),(1575,682)),((-83.0,104.0),(1454,719))]
def full(q):
    p = np.zeros(32); p[:9] = q[:9]; p[31] = q[9]; return p
def res(q, parts=False):
    p = full(q); h = q[10:14]; z2 = q[14:18]; z411 = q[18]; d = q[19]
    a = proj(p, inner); di = np.sqrt(((pin[:, None] - a[None]) ** 2).sum(-1)).min(1)
    o = proj(p, outer); do = np.sqrt(((pout[:, None] - o[None]) ** 2).sum(-1)).min(1)
    c = seat - d * (seat - [cxm, cym]) / np.linalg.norm(seat - [cxm, cym], axis=1)[:, None]
    g = proj(p, z3(c, 0.0)); dg = np.sqrt(((BL[:, None] - g[None]) ** 2).sum(-1)).min(1)
    dt = []
    for i, (hd, lo, base) in enumerate(TP):
        x, y = TWR[i][:2]
        dt += list(proj(p, [[x, y, h[i]]])[0] - hd) + list(proj(p, [[x, y, z2[i]]])[0] - lo)
        if base is not None: dt += list(proj(p, [[x, y, 0]])[0] - base)
    d4 = np.concatenate([proj(p, [[X[0], X[1], z411]])[0] - u for X, u in TW])
    R_ = [di * 0.4, do * 0.0, dg * 1.5, np.array(dt) * 1.0, d4 * 0.6]
    return R_ if parts else np.concatenate(R_)
P8 = json.load(open('camfit8.json'))['p']
q0 = list(P8[:9]) + [P8[31]] + [h for _, _, h in TWR] + [20, 20, 20, 20] + [60, 1.0]
lb = [-3e3, -3e3, 50, -7, -1.5, -0.3, 500, 600, 350, -0.3] + [40] * 4 + [-10] * 4 + [45, -2]
ub = [3e3, 3e3, 3e3, 7, -0.1, 0.3, 9000, 1000, 720, 0.9] + [130] * 4 + [120] * 4 + [70, 10]
s = least_squares(res, q0, bounds=(lb, ub), loss='soft_l1', f_scale=3)
R_ = res(s.x, True)
nm = ['inner', 'outer', 'seat', 'towers', '411']; w = [0.4, 0.3, 1.5, 1.0, 0.6]
for n, r, ww in zip(nm, R_, w): print(n, 'rms px', round(float(np.sqrt((r / ww) ** 2).mean() if False else np.sqrt(((r / ww) ** 2).mean())), 2), 'median', round(float(np.median(np.abs(r / ww))), 2))
print('tower res', np.round(R_[3].reshape(-1, 2), 1).tolist())
print('heights', np.round(s.x[10:14], 1).tolist(), 'z411', round(s.x[18], 1), 'seat offset', round(s.x[19], 2), 'k', round(s.x[9], 3))
p = full(s.x); json.dump({'p': list(p), 'q': list(s.x)}, open('camfit10.json', 'w'))
M = R(*p[3:6]); J = json.load(open('camB.json'))
json.dump({'C': p[:3].tolist(), 'M': M.tolist(), 'f': p[6], 'cx': p[7], 'cy': p[8], 'sun_az': J['sun_az'], 'sun_el': J['sun_el']}, open('camB6.json', 'w'))
