"""Check that nothing stands inside the boundary fence: python3 kit/clear.py <ground dir>.
Samples every straight stand's front edge, every building/box/poly corner, tower and screen; prints the
clearance (m) from the fence ellipse, negative = inside the field."""
import json, math, os, sys
import numpy as np
G = sys.argv[1].rstrip('/'); SLUG = os.path.basename(G); D = json.load(open(os.path.join(G, 'model', SLUG + '.json')))
x0, y0, a1, a2, rot = D['fence']; t = math.radians(rot); c, s = math.cos(t), math.sin(t)
def inside(p):   # >1 outside: the ellipse's own "radius" of a point
    q = np.array(p, float) - (x0, y0); u, v = c * q[0] + s * q[1], -s * q[0] + c * q[1]; return math.sqrt((u / a1) ** 2 + (v / a2) ** 2)
def clear(p):
    k = inside(p); r = math.hypot(p[0] - x0, p[1] - y0); return r - r / k
bad = []
def chk(name, pts):
    m = min(clear(p) for p in pts); print(f'{name:28s} {m:7.1f}'); (m < 1.0) and bad.append(name)
for S in D.get('stands', []):
    if S['kind'] == 'straight':
        A, B = np.array(S['a']), np.array(S['b']); chk('stand ' + S['name'], [A + (B - A) * f for f in np.linspace(0, 1, 41)])
E = D.get('extras', {})
for P in E.get('polys', []): chk('poly', P['p'])
for k in ('boxes', 'buildings', 'shelters'):
    for B in E.get(k, []):
        a = math.radians(B['a']); u = np.array([math.cos(a), math.sin(a)]); v = np.array([-u[1], u[0]]); cc = np.array(B['c'])
        chk(k, [cc + u * i * B['L'] / 2 + v * j * B['W'] / 2 for i in (-1, 1) for j in (-1, 1)])
for T in D.get('towers', []): chk('tower', [T['xy']])
print('INSIDE OR TOUCHING THE FENCE:', bad if bad else 'none')
