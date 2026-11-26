"""The fence of Cazaly's Stadium, measured on Google Earth (2026-11-22). Writes work/fence.json (the ellipse build.py uses)
and work/fence_trace.json (the measured points, model metres). No imagery is kept in the repo: the captures live in WORK.

  python3 tools/grounds/cazalys/qa/ge_compare.py plan cazalys WORK/v.json WORK     # v.json: --plan below writes it
  node tools/grounds/cazalys/qa/ge_shoot.js WORK                                   # 16 top-down captures round the fence
  python3 tools/grounds/cazalys/work/fence_ge.py WORK                              # trace, fit, report

Captures: straight down from 85 m, centred on the fence every 1/16 of the way round, picture up = outward. Google
Earth's top-down picture is a plain scale of the ground: F / range px per metre, F = 500 / tan(17.5 deg) (35 deg over
the 1000 px tall window; the capture keeps its middle 720 rows). Checked on the painted centre square: 50.0 m at 260 m
range, 49.8 m at 120 m.

Trace: each capture is straightened along the current ellipse (0.1 m along it, 0.02 m across it, -3..+3 m) and cut
into 2 m windows. In each window the grass is the median colour 1.5-3 m inside; the fence base is the first 0.2 m that
is not grass. Where the fence faces Google Earth's sun (outward normal within 70 deg of bearing 50) its shadow lies on
the grass: there the base is where the dark band ends at the bright top rail. Windows whose reference is not grass
(the interchange boxes in front of the grandstand) are skipped. Fit: ellipse, distance square to the curve, soft-L1
loss, points over 3 robust sigma dropped; re-straighten and repeat until it settles (4 rounds).

Result (2026-11-22): centre (-1.19, -3.69), semi-axes 75.21 x 87.49 m, long axis bearing 331.1 (rot 28.88 deg);
282/288 windows kept, error 0.32 m rms, 95% within 0.66 m. Adding radial harmonics (orders 3-8) did not hold up
when each capture was left out in turn, so the fence is this ellipse to within the trace's own noise. The OSM ellipse
the model used before (fence_osm.json) was 1.1 m rms off this trace, 2.5 m at worst (in on the north-west, out on the
south-east)."""
import json, math, os, sys
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
F = 500 / math.tan(math.radians(17.5))
SUN = 50.0


def xy2px(v, x, y):
    h = math.radians(v['h']); s = F / v['d']; dx, dy = x - v['at'][0], y - v['at'][1]
    return 640 + (dx * math.cos(h) - dy * math.sin(h)) * s, 360 - (dx * math.sin(h) + dy * math.cos(h)) * s


def ellipse(E, n=200001):
    x0, y0, a1, a2, rot = E; r = math.radians(rot); t = np.linspace(0, 2 * math.pi, n)
    u, v = a1 * np.cos(t), a2 * np.sin(t); X = x0 + u * math.cos(r) - v * math.sin(r); Y = y0 + u * math.sin(r) + v * math.cos(r)
    S = np.concatenate([[0], np.cumsum(np.hypot(np.diff(X), np.diff(Y)))])
    du, dv = -a1 * np.sin(t), a2 * np.cos(t); tx = du * math.cos(r) - dv * math.sin(r); ty = du * math.sin(r) + dv * math.cos(r)
    nn = np.hypot(tx, ty); return X, Y, S, ty / nn, -tx / nn


def dist(E, P):
    """signed distance square to the ellipse (+ outside)"""
    x0, y0, a1, a2, rot = E; r = math.radians(rot); c, s = math.cos(r), math.sin(r)
    u = (P[:, 0] - x0) * c + (P[:, 1] - y0) * s; v = -(P[:, 0] - x0) * s + (P[:, 1] - y0) * c; t = np.arctan2(v * a1, u * a2)
    for _ in range(30):
        ct, st = np.cos(t), np.sin(t); ex, ey = a1 * ct - u, a2 * st - v; dx, dy = -a1 * st, a2 * ct
        t = t - (ex * dx + ey * dy) / (dx * dx + dy * dy - ex * a1 * ct - ey * a2 * st)
    d = np.hypot(u - a1 * np.cos(t), v - a2 * np.sin(t)); return np.where((u / a1) ** 2 + (v / a2) ** 2 < 1, -d, d)


def trace(W, V, E):
    X, Y, S, NX, NY = ellipse(E); L = S[-1]; off = np.arange(3, -3.0001, -0.02); out = []
    from PIL import Image
    for vw in V:
        im = np.asarray(Image.open(os.path.join(W, 'ge', vw['name'] + '.png')).convert('RGB')).astype(float)
        s0 = S[np.argmin(np.hypot(X - vw['at'][0], Y - vw['at'][1]))]
        idx = np.searchsorted(S, (s0 - 20 + 0.1 * np.arange(400)) % L).clip(0, len(S) - 1)
        R = np.zeros((len(off), 400, 3))
        for j, o in enumerate(off):
            pp = np.array([xy2px(vw, X[i] + o * NX[i], Y[i] + o * NY[i]) for i in idx])
            for c in range(3): R[j, :, c] = map_coordinates(im[:, :, c], [pp[:, 1], pp[:, 0]], order=1, mode='nearest')
        for w0 in range(0, 400, 20):
            P = R[:, w0:w0 + 20].mean(1)[::-1]; o = off[::-1]
            g = P[o < -1.5]; mu = np.median(g, 0)
            if not (mu[1] > mu[0] + 5 and mu[1] > mu[2] + 5): continue
            sd = np.maximum(1.4826 * np.median(np.abs(g - mu), 0), 5); z = np.abs((P - mu) / sd).max(1); lum = P.mean(1); gl = mu.mean()
            e = next((i for i in range(np.where(o > -1.5)[0][0], len(o) - 10) if (z[i:i + 10] > 4).all()), None)
            if e is None: continue
            i = np.searchsorted(S, (s0 - 20 + 0.1 * (w0 + 10)) % L); nb = math.degrees(math.atan2(NX[i], NY[i])); kind = 'grass'
            if abs((nb - SUN + 180) % 360 - 180) < 70:
                dk = [k for k in range(e, min(e + 25, len(o) - 5)) if (lum[k:k + 5] < 0.65 * gl).all()]
                if dk:
                    j = dk[0]
                    while j < len(o) - 1 and lum[j] < 0.8 * gl: j += 1
                    if 0.3 <= o[j] - o[e] <= 1.4 and (lum[j:j + 10] > 1.1 * gl).any(): e = j; kind = 'shadow'
            out.append(dict(view=vw['name'], kind=kind, x=round(float(X[i] + o[e] * NX[i]), 3), y=round(float(Y[i] + o[e] * NY[i]), 3)))
    return out


def fit(P, E0):
    E = least_squares(lambda E: dist(E, P), E0, loss='soft_l1', f_scale=0.3).x
    for _ in range(2):
        d = dist(E, P); k = np.abs(d) < max(3 * 1.4826 * np.median(np.abs(d)), 0.6)
        E = least_squares(lambda E: dist(E, P[k]), E, loss='soft_l1', f_scale=0.3).x
    d = dist(E, P); k = np.abs(d) < max(3 * 1.4826 * np.median(np.abs(d)), 0.6); return E, d, k


def plan(W):
    E = json.load(open(os.path.join(HERE, 'fence_osm.json')))['ell']; x0, y0, a1, a2, rot = E; r = math.radians(rot); V = []
    for i in range(16):
        t = 2 * math.pi * i / 16; u, v = a1 * math.cos(t), a2 * math.sin(t)
        du, dv = -a1 * math.sin(t), a2 * math.cos(t); tx = du * math.cos(r) - dv * math.sin(r); ty = du * math.sin(r) + dv * math.cos(r)
        V.append(dict(name='f%02d' % i, h=round((math.degrees(math.atan2(tx, ty)) + 90) % 360, 1), t=0, d=85,
                      at=[round(x0 + u * math.cos(r) - v * math.sin(r), 2), round(y0 + u * math.sin(r) + v * math.cos(r), 2), 0]))
    json.dump(V, open(os.path.join(W, 'v.json'), 'w'), indent=0)


if __name__ == '__main__':
    W = sys.argv[1]
    if '--plan' in sys.argv: plan(W); sys.exit()
    V = json.load(open(os.path.join(W, 'v.json'))); E = json.load(open(os.path.join(HERE, 'fence_osm.json')))['ell']
    for it in range(5):
        T = trace(W, V, E); P = np.array([[t['x'], t['y']] for t in T]); E, d, k = fit(P, E)
        print('round %d: centre (%.2f, %.2f) semi %.2f x %.2f rot %.2f; %d/%d kept, rms %.2f m, p95 %.2f m' %
              (it, *E, k.sum(), len(P), np.sqrt((d[k] ** 2).mean()), np.percentile(np.abs(d[k]), 95)))
    dm = dist(json.load(open(os.path.join(HERE, 'fence_osm.json')))['ell'], P)
    print('OSM ellipse vs this trace: rms %.2f m, max %.2f m' % (np.sqrt((dm[k] ** 2).mean()), np.abs(dm[k]).max()))
    json.dump(dict(ell=list(E), src='Google Earth top-down trace of the fence base (work/fence_ge.py); the OSM fit is fence_osm.json'),
              open(os.path.join(HERE, 'fence.json'), 'w'), indent=1)
    for t, dd, kk in zip(T, d, k): t['resid'] = round(float(dd), 3); t['kept'] = bool(kk)
    json.dump(T, open(os.path.join(HERE, 'fence_trace.json'), 'w'), indent=0)
