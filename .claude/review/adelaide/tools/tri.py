"""triangulate a point seen in photo A and photo B: usage tri.py uA vA uB vB"""
import numpy as np, json, math, sys
def R(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
def ray(p, u, v):
    d = R(*p[3:6]).T @ np.array([(u - p[7]) / p[6], -(v - p[8]) / p[6], 1.0]); return np.array(p[:3]), d / np.linalg.norm(d)
pA = json.load(open('cam.json'))['p']; pB = json.load(open('camB.json'))['p']
uA, vA, uB, vB = map(float, sys.argv[1:5])
o1, d1 = ray(pA, uA, vA); o2, d2 = ray(pB, uB, vB)
w = o1 - o2; a, b, c, d, e = d1 @ d1, d1 @ d2, d2 @ d2, d1 @ w, d2 @ w
s = (b * e - c * d) / (a * c - b * b); t = (a * e - b * d) / (a * c - b * b)
P1, P2 = o1 + s * d1, o2 + t * d2
print('point', np.round((P1 + P2) / 2, 2), 'miss', round(float(np.linalg.norm(P1 - P2)), 2))
