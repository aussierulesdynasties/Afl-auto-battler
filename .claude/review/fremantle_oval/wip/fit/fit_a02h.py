import numpy as np, math, sys, json
sys.path.insert(0, 'fit'); from cam import *
from scipy.optimize import least_squares
src = open('fit/fit_hq3.py').read()
exec(src.split('h0 = [')[0])           # model, pts, OBS, horizon, TOW...
# HQ fixed at the g18 values (fit_g18d, eye height known): base 0.9, low eave +5.38, rise 1.96, tall eave +7.24, rise 2.10
H0 = dict(hl=6.28, rl=1.96, ht=8.14, rt=2.10, wl=5.79, w4=8.09, wt=5.73, w8=5.73, oh=1.0, hpe=8.14, hpr=10.5, Dp=10.0, Wp=7.0,
          sb0=3.7, sb1=6.4, sbz0=1.7, sbz1=3.35)
h = [H0[n] for n in NAMES]
W, H = DIM['a02']
def look(e, t, f):
    d = np.array(t) - np.array(e); return [*e, math.atan2(d[1], d[0]), math.atan2(d[2], math.hypot(d[0], d[1])), 0.0, f]
def run(shift, use_tower, obs):
    out = pts(h, None)
    def rc(p):
        r = []
        for key, i, x, y, w in obs:
            j = i + shift
            if key in ('talA',) and not (0 <= j < 5): continue
            if key == 'talV' and not (0 <= j < 5): continue
            X = out[key][j] if key in ('talA', 'talV') else out[key][i]
            r.extend((proj(list(p), np.array([X], float), W / 2, H / 2)[0] - np.array([x, y])) * w)
        r += list((horizon(p, W, H)[:, 1] - HY))
        r.append((p[6] - 2770.0) * 0.5)   # DJI FC2204 at 24 mm equivalent: about 2770 px on the 4000 x 3000 frame
        if use_tower:
            pb = proj(list(p), np.array([(*TOW, 0.0), (*TOW, 20.0)]), W / 2, H / 2)
            d = pb[1] - pb[0]; nn = np.array([-d[1], d[0]]) / np.linalg.norm(d)
            r += list((TOWLINE - pb[0]) @ nn)
        return np.array(r)
    bb = None
    for e in [(80, -30, 60), (60, 10, 50), (40, -10, 40), (90, 20, 80), (30, 20, 70), (0, 0, 60), (100, -20, 200), (60, 20, 120), (20, 0, 30), (0, 40, 80), (-30, 30, 60)]:
        for f in (2770,):
            try: r = least_squares(rc, look(e, (5, -96, 5), f), max_nfev=3000)
            except Exception: continue
            if bb is None or r.cost < bb.cost: bb = r
    return bb, rc
obs = [o for o in OBS['a02'] if o[0] in ('talA', 'talV')]
for use_tower in (False, True):
    for shift in (-2, -1, 0, 1):
        bb, rc = run(shift, use_tower, obs)
        print('tower', use_tower, 'shift', shift, 'rms', round(math.sqrt(2 * bb.cost / len(bb.fun)), 1), 'eye', np.round(bb.x[:3], 1),
              'yaw', round(math.degrees(bb.x[3]), 1), 'pitch', round(math.degrees(bb.x[4]), 1), 'f', round(bb.x[6]))
