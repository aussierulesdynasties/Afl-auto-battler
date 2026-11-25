"""Read a ring's height off Google Earth's oblique shots: sweep the ring's height, project it through the calibrated
camera (lines.py) and score each height by the brightness edge running along the projected line (the mean of the
gradient across the line, 1 px either side). The height where an edge runs along the whole ring wins. A sharp single
peak is a reading; a flat or double score is reported as no reading.

  python3 tools/grounds/mars/qa/heights.py <workdir>"""
import json, math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lines as LN, compare as C
B = LN.B

# (stand, ring, views): ring 'back' = the roof's back edge, 'front' = its front edge, 'fence' = the fence top
JOBS = [('fence', 'fence', ['low_e', 'from_w', 'bowl_s', 'from_nw']),
        ('west', 'back', ['low_e', 'from_w', 'from_nw', 'from_sw']),
        ('west', 'front', ['bowl_s', 'bowl_n', 'from_e', 'low_w']),
        ('north', 'front', ['bowl_s', 'from_s', 'from_se']),
        ('east', 'front', ['bowl_s', 'low_w', 'from_w', 'from_sw']),
        ('east', 'back', ['low_w', 'from_e', 'from_ne'])]


def ring_xy(stand, ring):
    if stand == 'fence':
        return [B.pol(b, B.fence_r(b)) for b in np.arange(0, 360, 0.5)]
    S = [s for s in B.D['stands'] if s['name'] == stand][0]
    k = 0 if ring == 'front' else 1
    return [B.pol(b, B.interp(S['roof'], b)[k]) for b in np.arange(S['b0'] + 2, S['b1'] - 2, 0.5)]


def score(g, cam, tgt, xy, z):
    P = np.array([(x, y, z) for x, y in xy]); px, dep = LN.project(cam, tgt, P)
    s = []
    for i in range(1, len(px) - 1):
        t = px[i + 1] - px[i - 1]; n = np.linalg.norm(t)
        if n < 1e-6 or dep[i] <= 0: continue
        nr = np.array([-t[1], t[0]]) / n; a = px[i] + nr * 1.5; b_ = px[i] - nr * 1.5
        if not all(2 <= q[0] < g.shape[1] - 2 and 70 <= q[1] < g.shape[0] - 2 for q in (a, b_)): continue
        s.append(abs(g[int(round(a[1])), int(round(a[0]))] - g[int(round(b_[1])), int(round(b_[0]))]))
    return (np.mean(s) if len(s) > 20 else np.nan), len(s)


def main(work):
    views = {v['name']: v for v in json.load(open(os.path.join(HERE, 'views.json')))}
    for v in views.values():
        a = v.get('at', [0, 0, 0]); v['at'] = [a[0] + C.FIT[0], a[1] - C.FIT[1], a[2]]
    out = {}
    for stand, ring, vs in JOBS:
        xy = ring_xy(stand, ring); zs = np.arange(0.0, 22.01, 0.2); reads = []
        for nm in vs:
            cam, tgt = LN.camera(views[nm], work)
            g = np.asarray(Image.open(os.path.join(work, 'ge', nm + '.png')).convert('L')).astype(float)
            sc = np.array([score(g, cam, tgt, xy, z)[0] for z in zs])
            if np.isnan(sc).all(): continue
            k = int(np.nanargmax(sc)); base = np.nanmedian(sc)
            # a reading needs a peak well above the typical score, and no rival peak 2 m away nearly as high
            far = np.abs(zs - zs[k]) > 2.0
            rival = np.nanmax(sc[far]) if far.any() else 0
            ok = sc[k] > 1.6 * base and sc[k] > 1.15 * rival
            reads.append((nm, round(float(zs[k]), 1), round(float(sc[k] / base), 2), ok))
        good = [r[1] for r in reads if r[3]]
        out['%s %s' % (stand, ring)] = {'reads': reads, 'z': round(float(np.median(good)), 1) if good else None}
        print(stand, ring, out['%s %s' % (stand, ring)])
    return out


if __name__ == '__main__':
    main(sys.argv[1])
