# Median photo colour of each seating tier per 10 deg of bearing, over every matched view that sees it.
# python work/colsamp.py
import sys, os, json, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, HERE); import earthcam
exec(open(os.path.join(HERE, 'seatgrid.py')).read().split("v, b0, b1, out")[0].split("import earthcam")[1])
TZ = {'t1': (-2.5, 3.5), 't2': (9.5, 14), 't3': (20, 29)}
def rz(b, z):
    p = prof(b); seg = [(p[0], p[1]), (p[3], p[4]), (p[6], p[7])]
    for (ra, za), (rb, zb) in seg:
        if za <= z <= zb: return ra + (rb - ra) * (z - za) / (zb - za)
    return np.nan
acc = {t: {k: [] for k in range(36)} for t in TZ}
for v in C:
    x0, y0, a, d, h, t = C[v]; c = earthcam.cam(h, t, d, tz=a - 13, tx=x0, ty=y0)
    I = np.asarray(Image.open(os.path.join(SP, 'ge', v + '.png')).convert('RGB')).astype(float)
    for tn, (za, zb) in TZ.items():
        for k in range(36):
            px = []
            for b in np.arange(k * 10 + 0.5, k * 10 + 10, 1.0):
                for z in np.linspace(za, zb, 5):
                    r = rz(b, z)
                    if np.isnan(r): continue
                    u, vv = earthcam.proj(c, (*pol(b, r), z))
                    if 0 <= u < 1919 and 90 <= vv < 1040: px.append(I[int(vv), int(u)])
            if len(px) > 20: acc[tn][k].append(np.median(np.array(px), 0))
for tn in TZ:
    print(tn)
    for k in range(36):
        L = acc[tn][k]
        if L: m = np.median(np.array(L), 0); print('  %3d %3d %3d %3d  n=%d' % (k * 10, *m, len(L)))
