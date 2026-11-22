# Relief displacement: in a top-down Google Earth shot from 3000 m a point z metres up shows (P - nadir) * z / H
# further out than it stands (about 0.6 m at the roof edges). The roof edges traced in edges.json are moved back by
# that, with each edge's measured height (stereo, heights.py) and the three shots' mean nadir (the registration
# point). Writes edges_true.json, which the fits read.
import json, math, numpy as np
C = json.load(open('cal.json')); DX, DY = C['dx'], C['dy']; H = 3000.0
E = json.load(open('edges.json'))
OLD = [(141.4, 172.2), (178.2, 205.8), (211.8, 239.3), (245.3, 272.3), (278.3, 309.3)]
def z_of(b, front):
    if b >= 315.3 or b <= 3.0:
        q = b if b >= 315.3 else b + 360
        return float(np.interp(q, [315.3, 330, 345, 363], [21.5, 21.3, 19.0, 18.0])) if front else 18.0
    if 77.0 <= b <= 135.4:
        return float(np.interp(b, [77, 106, 120, 135.4], [18.2, 18.4, 21.3, 21.3])) if front else 18.0
    arch = 0.0
    for a, c in OLD:
        if a <= b <= c: arch = 3.2 * math.sin(math.pi * (b - a) / (c - a))
    return (21.5 if front else 18.3) + arch
out = dict(E); moved = []
for key in ('rf', 'rb'):
    pts = []
    for b, r in E[key]:
        e, n = r * math.sin(math.radians(b)), r * math.cos(math.radians(b))
        k = z_of(b, key == 'rf') / H
        e2, n2 = e - (e - DX) * k, n - (n - DY) * k
        r2 = math.hypot(e2, n2); b2 = math.degrees(math.atan2(e2, n2)) % 360
        pts.append([b2, r2]); moved.append(r - r2)
    out[key] = pts
json.dump(out, open('edges_true.json', 'w'))
print('roof edges moved in by %.2f to %.2f m (median %.2f)' % (min(moved), max(moved), float(np.median(moved))))
