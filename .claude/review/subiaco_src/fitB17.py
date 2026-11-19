# Refit photo 17's camera in the turned (C6) frame from the four light towers (stood 1997-2019), heads at TH, bases z 0.
# Start = camB turned 180 deg about (0.25,10.22) (via point turning). Writes camB17.json (points pre-turned NOT needed).
import json, math, numpy as np
from scipy.optimize import least_squares
from camlib import proj
L = json.load(open('layoutC6.json')); A = json.load(open('layoutA.json')); co = A['fence']['co']; K = A['fence']['K']; C0 = A['C0']
TH = L['TH']; PV = np.array([0.25, 10.22])
def rf(a):
    t = math.radians(a); return sum(co[k] * math.cos(k * t) for k in range(K + 1)) + sum(co[K + k] * math.sin(k * t) for k in range(1, K + 1))
def P(a, d, z):
    r = rf(a) + d; t = math.radians(a); return [C0[0] + r * math.cos(t), C0[1] + r * math.sin(t), z]
camB = json.load(open('camB.json'))['p'][:7]
def turn(X): X = np.array(X, float); X[:, :2] = 2 * PV - X[:, :2]; return X
obs = {'head': [(145, 95), (272, 265), (683, 35), (877, 168)], 'base': [None, (267, 508), (682, 182), (871, 322)]}
import os
if os.environ.get('SAT'):
    hx,hy=-25.0,-66.5;bx,by=hx-0.353*TH,hy-0.098*TH;a=math.degrees(math.atan2(by-C0[1],bx-C0[0]));L['TOW'][2]=[a,math.hypot(bx-C0[0],by-C0[1])-rf(a)]
heads = np.array([P(a, d, TH) for a, d in L['TOW']]); bases = np.array([P(a, d, 0) for a, d in L['TOW']])
ph = proj(camB, turn(heads), 500, 300)
order = [int(np.argmin([np.hypot(*(ph[i] - o)) for i in range(4)])) for o in obs['head']]
print('tower order', order, ph.round())
X, U = [], []
for j, i in enumerate(order):
    X.append(heads[i]); U.append(obs['head'][j])
    if obs['base'][j]: X.append(bases[i]); U.append(obs['base'][j])
X = np.array(X); U = np.array(U, float)
# turned camera as a start: camera centre turned, then solve orientation by fit
c = camB[:]; c[0], c[1] = 2 * PV - np.array(camB[:2])
FF=os.environ.get('FREEF')
def res(p): return (proj(list(p[:6]) + [p[6] if FF else camB[6]], X, 500, 300) - U).ravel()
best = None
for dy in np.radians(np.arange(0, 360, 30)):
    s = c[:6] + ([camB[6]] if FF else []); s[3] = camB[3] + dy
    r = least_squares(res, s, x_scale=[50, 50, 50, .1, .1, .1] + ([500] if FF else []))
    if best is None or r.cost < best.cost: best = r
p = list(best.x[:6]) + [best.x[6] if FF else camB[6]]; e = res(best.x).reshape(-1, 2)
print('rms px', np.sqrt((e ** 2).sum(1).mean()).round(2), 'per point', np.hypot(*e.T).round(1))
json.dump({'p': p, 'W': 1000, 'H': 600, 'note': 'fitB17: four light towers in the turned C6 frame'}, open('camB17.json', 'w', newline=''))
