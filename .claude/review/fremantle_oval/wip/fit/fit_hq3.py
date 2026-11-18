import numpy as np, math, sys, json
sys.path.insert(0, 'fit'); from cam import *
from scipy.optimize import least_squares
# joint fit: HQ shape shared by g18, g34 and a02; one camera per photo. Model frame as in build.py hq():
# per-gable chord A=at(S[k]) -> B=at(S[k+1]), u along it, n = (-u.y, u.x) into the building, P(a, d, z) = A + u a + n d.
F = [(31.0, -98.1), (27.3, -98.9), (22.9, -99.3), (17.9, -99.5), (12.2, -99.3), (7.6, -98.9), (2.9, -98.2),
     (-2.8, -97.0), (-7.7, -95.2), (-13.5, -92.9), (-18.0, -90.3), (-21.4, -88.1)]
def at(s):
    acc = 0.0
    for i in range(len(F) - 1):
        a, b = np.array(F[i]), np.array(F[i + 1]); L = np.linalg.norm(b - a)
        if s <= acc + L or i == len(F) - 2: return a + (b - a) * (s - acc) / L
        acc += L
ZB = 0.9
NAMES = ['hl', 'rl', 'ht', 'rt', 'wl', 'w4', 'wt', 'w8', 'oh', 'hpe', 'hpr', 'Dp', 'Wp', 'sb0', 'sb1', 'sbz0', 'sbz1']
def model(h):
    hd = dict(zip(NAMES, h))
    S = [0.0]
    for k in range(10): S.append(S[-1] + (hd['wl'] if k < 4 else hd['w4'] if k == 4 else hd['wt'] if k < 8 else hd['w8'] if k == 8 else hd['Wp']))
    def P(k, a, d, z):
        A = at(S[k]); B = at(S[k + 1])   # at() runs on along the last chord past the OSM front's end
        u = (B - A) / np.linalg.norm(B - A); n = np.array([-u[1], u[0]])
        p = A + u * a + n * d; return (p[0], p[1], z)
    return hd, S, P
def pts(h, which):
    hd, S, P = model(h); W_ = lambda k: S[k + 1] - S[k]; oh = hd['oh']
    lowA = lambda k: P(k, W_(k) / 2, -oh, hd['hl'] + hd['rl'])
    talA = lambda k: P(k, W_(k) / 2, -oh, hd['ht'] + hd['rt'])
    out = {}
    out['lowA'] = [lowA(k) for k in range(4)]
    out['lowV'] = [P(k, 0, -oh, hd['hl']) for k in range(5)]        # valley tips k 0..4 (k 0 = east end eave)
    out['foot'] = [P(k, 0, 0, ZB) for k in range(9)]                 # column bases at the valleys
    out['talA'] = [talA(k) for k in range(4, 9)]                     # apexes of gables 5..9 (k 4..8)
    out['talV'] = [P(k, 0, -oh, hd['ht']) for k in range(5, 10)]     # valleys k 5..9 (k 9 = end of gable 9)
    out['pW'] = [P(9, W_(9), -oh, hd['hpe']), P(9, W_(9), hd['Dp'] / 2, hd['hpr']), P(9, W_(9), hd['Dp'], hd['hpe'])]
    out['sb'] = [P(4, hd['sb0'], -0.25, ZB + hd['sbz1']), P(4, hd['sb1'], -0.25, ZB + hd['sbz1']),
                 P(4, hd['sb1'], -0.25, ZB + hd['sbz0']), P(4, hd['sb0'], -0.25, ZB + hd['sbz0'])]
    return out
# ---------------- observations: (key, index, x, y, weight)
def full18(x2, y2): return (x2 / 2 + 480, y2 / 2 + 380)
OBS = {'g18': [], 'g34': [], 'a02': []}
for i, b in enumerate([(45,512),(213,512),(381,512),(545,508),(708,505),(940,497),(1097,495),(1250,493),(1393,490)]):
    OBS['g18'].append(('foot', i, *full18(*b), 1.0))
for i, b in enumerate([(45,318),(213,300),(381,290),(545,282),(708,275)]): OBS['g18'].append(('lowV', i, *full18(*b), 1.0))
for i, b in enumerate([(130,232),(300,222),(465,212),(635,198)]): OBS['g18'].append(('lowA', i, *full18(*b), 1.0))
for i, b in enumerate([(940,185),(1097,165),(1250,145),(1393,111)]): OBS['g18'].append(('talV', i, *full18(*b), 1.0))
for i, b in enumerate([(1015,75),(1160,52),(1320,28)]): OBS['g18'].append(('talA', i + 1, *full18(*b), 1.0))
G34 = OBS['g34']
for i, b in enumerate([(526,390.5),(579,389.5),(631,388),(681,387)]): G34.append(('lowA', i, *b, 1.0))
for i, b in enumerate([(552.5,408.3),(605,407.5),(655.8,406.7),(706.7,405)]): G34.append(('lowV', i + 1, *b, 1.0))
for i, b in enumerate([(555,464),(606.7,464),(656.7,463.5),(705.8,463.3)]): G34.append(('foot', i + 1, *b, 1.0))
for i, b in enumerate([(754,363.6),(803.6,361),(848,359),(893,355.6),(936.6,352.4)]): G34.append(('talA', i, *b, 1.0))
for i, b in enumerate([(778.6,382.4),(825.4,380),(871,377.6),(915.6,375.4)]): G34.append(('talV', i, *b, 1.0))
G34 += [('pW', 0, 1030, 368, 0.5), ('pW', 1, 1058.5, 346.5, 0.5), ('pW', 2, 1092, 375.5, 0.5)]
G34 += [('sb', 1, 763, 422, 0.7), ('sb', 2, 763, 438, 0.7)]
A02 = OBS['a02']
for i, b in enumerate([(240,1622),(452,1600),(655,1582),(847,1565),(1035,1575)]): A02.append(('talA', i, *b, 1.0 if i < 4 else 0.5))
for i, b in enumerate([(360,1720),(557,1695),(742,1677),(925,1660),(1117,1655)]): A02.append(('talV', i, *b, 1.0 if i < 4 else 0.5))
A02 += [('lowV', 4, 40, 1820, 0.7)]
A02 += [('sb', 0, 220, 1845, 0.7), ('sb', 1, 318, 1842, 0.7), ('sb', 2, 318, 1882, 0.7), ('sb', 3, 222, 1899, 0.7)]
DIM = {'g18': (1400, 1031), 'g34': (2048, 1365), 'a02': (2408, 2992)}
PH = ['g18', 'g34', 'a02']
NH = len(NAMES)
TOWLINE = np.array([(1660, 1155), (1676, 1625)], float); TOW = (-87.7, -36.4); HY = 966
def horizon(p, W, H):
    C = np.array(p[:3]); dip = math.sqrt(2 * max(p[2], 1) / 6.371e6)
    P_ = [C + np.array([math.cos(p[3] + da), math.sin(p[3] + da), -dip]) * 1e6 for da in np.linspace(-0.25, 0.25, 5)]
    return proj(list(p), np.array(P_), W / 2, H / 2)
def extra(cs):
    r = []
    r.append((cs['g18'][2] - 3.2) * 3)          # g18 eye: the photo-mode height already checked against g18 (1.6 + 1.63)
    r.append((cs['g34'][2] - 2.0) * 0.3)        # g34: taken from the field side, eye a little above the grass
    W, H = DIM['a02']; p = cs['a02']
    r += list((horizon(p, W, H)[:, 1] - HY) * 1.0)   # a02: the sea horizon
    pb = proj(list(p), np.array([(*TOW, 0.0), (*TOW, 20.0)]), W / 2, H / 2)
    d = pb[1] - pb[0]; nn = np.array([-d[1], d[0]]) / np.linalg.norm(d)
    r += list(((TOWLINE - pb[0]) @ nn) * 1.0)   # a02: the SW light tower's pole lies on its line
    return r
def cams(q): return {ph: q[NH + 7 * i: NH + 7 * i + 7] for i, ph in enumerate(PH)}
def res(q):
    h = q[:NH]; r = []
    for ph, p in cams(q).items():
        W, H = DIM[ph]; out = None
        for key, i, x, y, w in OBS[ph]:
            if out is None: out = pts(h, None)
            X = np.array([out[key][i]], float)
            d = proj(list(p), X, W / 2, H / 2)[0] - np.array([x, y]); r.extend(d * w)
        if ph == 'g18':   # horizon from the g18 crop (far point at eye height lands on y 577)
            far = np.array([[p[0] + 1e5 * math.cos(p[3]), p[1] + 1e5 * math.sin(p[3]), p[2]]])
            r.append((proj(list(p), far, W / 2, H / 2)[0, 1] - 577.0) * 3)
    r += extra(cams(q))
    # weak priors: keep unobserved shape values near the model's
    r += [(q[NAMES.index('Dp')] - 10.0) * 0.5, (q[NAMES.index('Wp')] - 7.0) * 0.2]
    return np.array(r)
h0 = [6.2, 2.0, 8.0, 2.15, 5.8, 8.1, 5.75, 5.75, 1.0, 8.0, 10.5, 10.0, 7.0, 3.7, 6.4, 1.7, 3.35]
g18 = json.load(open('fit/cam_g18.json'))['p']; g18 = list(g18); g18[2] = 3.2
def cam_only(ph, c0, h):
    W, H = DIM[ph]; out = pts(h, None)
    def rc(p):
        r = []
        for key, i, x, y, w in OBS[ph]:
            r.extend((proj(list(p), np.array([out[key][i]], float), W / 2, H / 2)[0] - np.array([x, y])) * w)
        cs = {k_: C.get(k_, c0) for k_ in PH}; cs[ph] = p
        if ph == 'a02':
            pb = proj(list(p), np.array([(*TOW, 0.0), (*TOW, 20.0)]), W / 2, H / 2)
            d = pb[1] - pb[0]; nn = np.array([-d[1], d[0]]) / np.linalg.norm(d)
            r += list((horizon(p, W, H)[:, 1] - HY)) + list((TOWLINE - pb[0]) @ nn)
        else: r.append((p[2] - 2.0) * 0.3)
        return np.array(r)
    return least_squares(rc, c0, max_nfev=3000)
def look(e, t, f):
    d = np.array(t) - np.array(e); return [*e, math.atan2(d[1], d[0]), math.atan2(d[2], math.hypot(d[0], d[1])), 0.0, f]
C = {'g18': g18}
for ph, eyes, fs in (('g34', [(-58, 30, 2), (-40, 40, 2), (-20, 40, 2), (-70, 0, 2), (0, 30, 2), (-30, 0, 2)], (2500, 4000, 6000)),
                     ('a02', [(80, -30, 60), (60, 10, 50), (40, -10, 40), (90, 20, 80), (30, 20, 70), (0, 0, 60), (100, -20, 200), (60, 20, 120), (20, 0, 30)], (1500, 2500, 4000))):
    bb = None
    for e in eyes:
        for f in fs:
            try: r = cam_only(ph, look(e, (5, -96, 5), f), h0)
            except Exception: continue
            if bb is None or r.cost < bb.cost: bb = r
    C[ph] = list(bb.x); print(ph, 'alone rms', round(math.sqrt(2 * bb.cost / len(bb.fun)), 2), np.round(bb.x[:3], 1))
q0 = h0 + C['g18'] + C['g34'] + C['a02']
best = least_squares(res, q0, max_nfev=20000)
q = best.x
print('rms', round(math.sqrt(2 * best.cost / len(best.fun)), 2))
for nm, v in zip(NAMES, q[:NH]): print(f'  {nm} {v:.2f}')
k = 0
for ph, p in cams(q).items():
    n_ = len(OBS[ph]); rr = best.fun[k:k + 2 * n_].reshape(-1, 2); k += 2 * n_ + (1 if ph == 'g18' else 0)
    print(ph, 'eye', np.round(p[:3], 1), 'yaw', round(math.degrees(p[3]), 1), 'pitch', round(math.degrees(p[4]), 1), 'roll', round(math.degrees(p[5]), 1), 'f', round(p[6]))
    print('  ', [(o[0][:4] + str(o[1]), tuple(np.round(e, 1))) for o, e in zip(OBS[ph], rr)])
    W, H = DIM[ph]
    json.dump({'p': list(map(float, p)), 'W': W, 'H': H}, open(f'fit/cam_{ph}h.json', 'w'))
json.dump(dict(zip(NAMES, map(float, q[:NH]))), open('fit/hq3.json', 'w'), indent=1)
