import os, json, math
import numpy as np
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(SP, 'model', 'mcg.json')))


def pol(b, r):
    a = math.radians(b); return (r * math.sin(a), r * math.cos(a))


def foot(b):
    best = 0
    for k in ('shane_warne', 'mcc', 'olympic', 'ponsford'):
        P = np.array(D['osm'][k], float); d = np.array(pol(b, 1.0))
        for a, c in zip(P, np.roll(P, -1, 0)):
            e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-9: continue
            t, s = np.linalg.solve(M, a)
            if t > 0 and 0 <= s <= 1: best = max(best, t)
    return best


