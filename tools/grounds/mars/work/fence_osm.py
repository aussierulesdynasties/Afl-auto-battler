# The boundary fence = the OSM AFL pitch outline (way 128280660, ODbL), one radius per degree from the origin (cw from
# north). It agrees with the published 160 x 129 m boundary plus the usual ~5.5 m run-off. The earlier trace off the
# Esri tile (fence.py) stopped where the grass turns brown and worn, 5 m short at the ends. Writes work/fence.json.
import os, json, math, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo
W = {w['id']: w for w in json.load(open(os.path.join(HERE, '..', 'osm', 'near.json')))['ways']}
P = np.array([geo.ll2xy(*p) for p in W[128280660]['ll']])


def radius(b):
    a = math.radians(b); d = np.array([math.sin(a), math.cos(a)]); best = None
    for p, q in zip(P[:-1], P[1:]):
        e = q - p; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-9: continue
        t, s = np.linalg.solve(M, p)
        if t > 0 and 0 <= s <= 1: best = t if best is None else max(best, t)
    return best


fr = np.array([radius(b) for b in range(360)])
k = np.array([1, 2, 3, 2, 1], float); k /= k.sum()          # the mapped corners smoothed over 5 degrees
fr = np.convolve(np.r_[fr[-2:], fr, fr[:2]], k, 'valid')
json.dump({'source': 'OSM way 128280660', 'fr': [round(float(r), 2) for r in fr]}, open(os.path.join(HERE, 'fence.json'), 'w'))
print('fence radius min/max', fr.min().round(1), fr.max().round(1))
