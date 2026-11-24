# The east roof's front edge at its north end (72 to 86 deg). The general trace (edges.py) stops there on a pale
# concrete landing in front of the roof; here the edge is the first rise through 150 (the gutter's grey, as
# everywhere else) after the last dip under 125 between 72 and 90 m, in the same whiteness profiles, moved in for
# relief like relief.py. The points replace edges_true.json's roof front points in that range.
import json, math, numpy as np
from scipy.ndimage import gaussian_filter1d
C = json.load(open('cal.json')); DX, DY = C['dx'], C['dy']; H = 3000.0; Z = 18.2
P = json.load(open('profiles.json')); r0, r1, st = P['rs']; rs = np.arange(r0, r1, st)
E = json.load(open('edges_true.json'))
pts = []
for b in np.arange(72.0, 86.01, 0.5):
    L = gaussian_filter1d(np.array(P['L'][str(float(b))]), 2); m = (rs >= 72) & (rs <= 90)
    idx = np.where(m)[0]; dips = [i for i in idx if L[i] < 125]
    if not dips: continue
    j = next((i for i in range(dips[-1], idx[-1]) if L[i] < 150 <= L[i + 1]), None)
    if j is None: continue
    r = rs[j] + (150 - L[j]) / (L[j + 1] - L[j]) * st
    e, n = r * math.sin(math.radians(b)), r * math.cos(math.radians(b)); k = Z / H
    e, n = e - (e - DX) * k, n - (n - DY) * k
    pts.append([math.degrees(math.atan2(e, n)) % 360, math.hypot(e, n)])
E['rf'] = [p for p in E['rf'] if not 72.0 <= p[0] <= 86.2] + pts
json.dump(E, open('edges_true.json', 'w'))
print('east roof north corner: %d points' % len(pts), [(round(b, 1), round(r, 1)) for b, r in pts[::4]])
