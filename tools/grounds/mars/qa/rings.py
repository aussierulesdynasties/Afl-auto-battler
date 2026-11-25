"""Measure each stand's roof edges in Google Earth's straight-down tiles as distances out from the fence curve, and
compare them with the model's plan (model/mars.json), in metres.

  python3 tools/grounds/mars/qa/rings.py <workdir>

Along each 0.5 deg ray the roof is the first white run wider than 3 m past the fence; its near and far ends are the
roof's front and back edges. A roof stands h metres up, so a straight-down camera H = 330 m above the turf sees it
pushed out from the picture's centre by h / (H - h) of its distance; that is taken back out with the model's roof
heights (z_roof front and back). Each edge is then its distance from the fence along the fence's normal. Prints,
per stand, Google Earth's median and spread, the model's, and the difference."""
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'model'))
import trace as T
from fit import dist_to

H = 330.0


def curve():
    C = json.load(open(os.path.join(HERE, 'fence_curve.json'))); fc = C['centre']
    b = np.radians([q[0] for q in C['bearing_r']]); r = np.array([q[1] for q in C['bearing_r']])
    return fc[0] + r * np.sin(b), fc[1] + r * np.cos(b)


def offset(px, py, cx, cy):
    d = dist_to(np.array([px]), np.array([py]), cx, cy)[0]
    # outside the fence when further from the field centre than the curve on that bearing
    fc = (-4.18, -4.88); b = math.atan2(px - fc[0], py - fc[1]) % (2 * math.pi)
    cb = np.arctan2(cx - fc[0], cy - fc[1]) % (2 * math.pi); o = np.argsort(cb)
    rc = np.interp(b, cb[o], np.hypot(cx - fc[0], cy - fc[1])[o], period=2 * math.pi)
    return d if math.hypot(px - fc[0], py - fc[1]) > rc else -d


def roof_edges(t, b, hz):
    e0, n0, G, ok, Wt, L = t
    a = math.radians(b); st = 0.05; rs = np.arange(40.0, 125.0, st)
    E = T.FC[0] + rs * math.sin(a); N = T.FC[1] + rs * math.cos(a)
    u = np.round(640 + (E - e0) / T.S).astype(int); v = np.round(500 - (N - n0) / T.S - 140).astype(int)
    if not ((u >= 0) & (u < G.shape[1]) & (v >= 0) & (v < G.shape[0])).all() or not ok[v, u].all():
        return None
    w = Wt[v, u]; g = G[v, u]; started = False
    for k in range(len(rs)):
        if g[k]: started = True; continue
        if started and w[k]:
            j = k
            while j < len(rs) and (w[j] or (j + 6 < len(rs) and w[j:j + 6].any())): j += 1   # bridge skylights < 0.3 m
            if (j - k) * st > 3.0:
                out = []
                for kk, h in ((k, hz[0]), (j - 1, hz[1])):
                    ae, an = E[kk] - e0, N[kk] - n0                 # from the nadir, as seen
                    f = (H - h) / H
                    out.append((e0 + ae * f, n0 + an * f))
                return out
    return None


def main(work):
    import build as B
    D = B.D                                             # the plan as the build uses it (after unlean)
    cx, cy = curve()
    names = sorted(f[:-4] for f in os.listdir(os.path.join(work, 'ge')) if f.startswith('trace_') and f.endswith('.png') and '_cam' not in f)
    tiles = [T.tile(work, n) for n in names]
    rep = {}
    for S in D['stands']:
        if 'roof' not in S: continue
        hz = S.get('z_roof', [15, 15])
        res = {'front': [], 'back': [], 'm_front': [], 'm_back': []}
        for b in np.arange(S['b0'] + 2, S['b1'] - 2, 0.5):
            hits = [h for h in (roof_edges(t, b % 360, hz) for t in tiles) if h]
            if not hits: continue
            fo = np.median([offset(*h[0], cx, cy) for h in hits]); bo = np.median([offset(*h[1], cx, cy) for h in hits])
            ri, ro = B.interp(S['roof'], b)
            res['front'].append(fo); res['back'].append(bo)
            res['m_front'].append(ri - B.fence_r(b % 360)); res['m_back'].append(ro - B.fence_r(b % 360))
        if not res['front']: continue
        r = {k: (round(float(np.median(v)), 2), round(float(np.percentile(v, 90) - np.percentile(v, 10)), 2)) for k, v in res.items()}
        r['n'] = len(res['front'])
        r['d_front'] = round(float(np.median(np.array(res['m_front']) - np.array(res['front']))), 2)
        r['d_back'] = round(float(np.median(np.array(res['m_back']) - np.array(res['back']))), 2)
        rep[S['name']] = r
        print(S['name'], json.dumps(r))
    return rep


if __name__ == '__main__':
    main(sys.argv[1])
