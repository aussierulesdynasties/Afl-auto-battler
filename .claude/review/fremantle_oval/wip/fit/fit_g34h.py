import numpy as np, math, sys, json
sys.path.insert(0, 'fit'); from cam import *
from scipy.optimize import least_squares
exec(open('fit/fit_a02h.py').read().split("W, H = DIM['a02']")[0])
H0['rt'] = 2.35; h = [H0[n] for n in NAMES]
W, H = DIM['g34']; out = pts(h, None)
obs = [o for o in OBS['g34'] if o[0] in ('lowA', 'lowV', 'foot', 'talA', 'talV', 'sb')]
obs = [o for o in obs if not (o[0] == 'talA' and o[1] == 4)]
def rc(p):
    r = []
    for key, i, x, y, w in obs:
        r.extend((proj(list(p), np.array([out[key][i]], float), W / 2, H / 2)[0] - np.array([x, y])) * w)
    r.append((p[2] - 2.0) * 1.0)
    return np.array(r)
def look(e, t, f):
    d = np.array(t) - np.array(e); return [*e, math.atan2(d[1], d[0]), math.atan2(d[2], math.hypot(d[0], d[1])), 0.0, f]
bb = None
for e in [(-58, 30, 2), (-40, 40, 2), (-20, 60, 2), (-70, 0, 2), (0, 40, 2), (-30, 0, 2), (-80, 60, 3), (10, 80, 3)]:
    for f in (2000, 3000, 4500, 6000):
        r = least_squares(rc, look(e, (5, -96, 5), f), max_nfev=3000)
        if bb is None or r.cost < bb.cost: bb = r
print('rms', round(math.sqrt(2 * bb.cost / len(bb.fun)), 2), np.round(bb.x[:3], 1), 'yaw', round(math.degrees(bb.x[3]), 1), 'pitch', round(math.degrees(bb.x[4]), 2), 'f', round(bb.x[6]))
print([(o[0] + str(o[1]), tuple(np.round(e, 1))) for o, e in zip(obs, bb.fun.reshape(-1, 2) if len(bb.fun) % 2 == 0 else bb.fun[:-1].reshape(-1, 2))])
json.dump({'p': list(map(float, bb.x)), 'W': W, 'H': H}, open('fit/cam_g34h.json', 'w'))
