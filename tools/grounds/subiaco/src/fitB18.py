# Photo 17 camera in the turned (C6) frame: grass edge (as fitB.py: fence = boundary + mg) plus the four light-tower
# heads/bases at their C6 positions. Works in camB's old frame (points turned 180 deg about (0.25,10.22) before projecting),
# then writes camB18.json holding the old-frame camera and 'turn': true.
import json, math, os, numpy as np
from scipy.optimize import least_squares
from camlib import *
exec(open('fitB.py').read().split('def res(')[0])            # ED, fence(mg), PITCH frame from fitB.py
LC = json.load(open('layoutC6.json')); A = json.load(open('layoutA.json')); coA = A['fence']['co']; KA = A['fence']['K']; C0 = A['C0']
TH = LC['TH']; PV = np.array([0.25, 10.22])
def rfa(a):
    t = math.radians(a); return sum(coA[k] * math.cos(k * t) for k in range(KA + 1)) + sum(coA[KA + k] * math.sin(k * t) for k in range(1, KA + 1))
def Pt(a, d, z):
    r = rfa(a) + d; t = math.radians(a); return [C0[0] + r * math.cos(t), C0[1] + r * math.sin(t), z]
def turn(X): X = np.array(X, float); X[:, :2] = 2 * PV - X[:, :2]; return X
TOWO = [(272, 265, 267, 508), (145, 95, None, None), (877, 168, 871, 322), (683, 35, 682, 182)]   # TOW index 0..3
X, UO = [], []
for (a, d), (hu, hv, bu, bv) in zip(LC['TOW'], TOWO):
    X.append(Pt(a, d, TH)); UO.append((hu, hv))
    if bu: X.append(Pt(a, d, 0)); UO.append((bu, bv))
XT = turn(X); UO = np.array(UO, float)
W8 = float(os.environ.get('WT', 1.0))
def res(p, full=False):
    cam = list(p[:7]); mg = p[7]
    r1 = curve_d(ED, proj(cam, np.c_[fence(mg), np.zeros(len(fence(mg)))], cx, cy))
    r2 = (proj(cam, XT, cx, cy) - UO).ravel()
    return (r1, r2) if full else np.concatenate([r1, r2 * W8, [(mg - 6) * 0.1]])
cB = json.load(open('camB.json')); p0 = np.r_[cB['p'][:7], cB['mg']]
sol = least_squares(lambda q: res(np.r_[q[:6], p0[6], q[6]]), np.r_[p0[:6], p0[7]], loss='soft_l1', f_scale=3, max_nfev=2000)
p = np.r_[sol.x[:6], p0[6], sol.x[6]]; r1, r2 = res(p, True); e = np.hypot(*r2.reshape(-1, 2).T)
print('edge med px', np.median(np.abs(r1)).round(2), 'towers px', e.round(1), 'mg', p[7].round(2))
json.dump({'p': list(p[:7]) + [1.0], 'W': 1000, 'H': 600, 'mg': p[7], 'turn': True,
           'note': 'fitB18: grass edge + 4 towers; project turn(X) (180 deg about 0.25,10.22)'}, open('camB18.json', 'w', newline=''))
