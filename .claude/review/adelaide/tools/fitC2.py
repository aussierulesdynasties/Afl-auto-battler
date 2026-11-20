"""camera C from points: tower collars + frame centres (model geometry) + lawn NW corner (Esri), weak prior on
the camera's plan position from Esri (on the plaza north of the lawn). Writes camC3.json."""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from projC import R
from esri import px2m
from scipy.optimize import least_squares
sp = json.load(open('spec.json')); T = sp['towers']
PC = np.array(json.loads(os.environ.get('PC', '[0,0]')), float)
def tw(x, y):
    d2 = PC - [x, y]; d2 /= np.linalg.norm(d2); dv = np.r_[d2, 0]; up = np.array([0, 0, 1.0])
    K = np.array([x, y, T['kink']])
    eb = math.radians(T['elbow_lean']); E = K + (up * math.cos(eb) - dv * math.sin(eb)) * T['elbow_len']
    ln = math.radians(T['neck_lean']); nd = up * math.cos(ln) + dv * math.sin(ln); fn = dv * math.cos(ln) - up * math.sin(ln)
    return np.array([x, y, T['kink'] - T['collar']]), E + fn * (T['frame_off'] + T['bow']) + nd * T['frame_len'] / 2
SE = tw(105.29, -75.82); NE = tw(65.65, 112.08)
lawn = px2m(1461, 1137)
X = np.array([SE[0], SE[1], NE[0], NE[1], [lawn[0], lawn[1], 0.0]])
U = np.array([(490, 432), (530, 305), (3425, 716), (3410, 615), (975 * 2.4, 590 * 2.4)], float)
prior = np.array(json.loads(os.environ.get('PRIOR', '[195,5]')))
def proj(p, X):
    d = (X - p[:3]) @ R(*p[3:6]).T
    return np.stack([1920 + p[6] * d[:, 0] / d[:, 2], p[7] - p[6] * d[:, 1] / d[:, 2]], 1)
def res(q):
    return np.r_[(proj(q, X) - U).ravel(), (q[:2] - prior) * float(os.environ.get('PW', '3')),
                 (q[2] - 1.6) * float(os.environ.get('ZW','2')), q[4] * 3000, q[5] * 3000]   # verticals corrected: pitch=roll=0
q0 = np.r_[prior, 1.6, math.pi, 0.0, 0.0, 1500, 1080]
r = least_squares(res, q0)
q = r.x; print('C', np.round(q[:3], 1), 'yaw', round(math.degrees(q[3]), 1), 'pitch', round(math.degrees(q[4]), 2), 'roll', round(math.degrees(q[5]), 2), 'f', round(q[6]), 'cy', round(q[7]))
print('px err', np.round(proj(q, X) - U, 1).tolist())
json.dump({'p': [*q[:7], 1920.0, q[7]], 'W': 3840, 'Himg': 2160}, open('camC3.json', 'w'))
