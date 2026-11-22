# Fence = outer edge of the grass on the Esri tile, per bearing (cw from north). Writes work/fence.json [[b,r],...] every 2 deg,
# plus an ellipse fit (centre, semi-axes, rotation) so the trace can be checked for lumps.
import os, json, math
import numpy as np
from PIL import Image
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = np.asarray(Image.open(os.path.join(SP, 'sat', 'esri_025.png')).convert('RGB')).astype(int)
def px(x, y):
    u = int(round((x + 260) * 4)); v = int(round((260 - y) * 4)); return S[v, u]
out = []
for b in np.arange(0, 360, 1.0):
    a = math.radians(b); run = 0; rr = None
    for r in np.arange(55, 110, 0.25):
        R, G, B = px(r * math.sin(a), r * math.cos(a))
        grass = G > R + 12 and G > B + 8
        if not grass:
            run += 1
            if run >= 6: rr = r - 6 * 0.25 + 0.25; break
        else: run = 0
    out.append([float(b), rr])
def fit(out):
    pts = np.array([[r * math.sin(math.radians(b)), r * math.cos(math.radians(b))] for b, r in out if r])
    x, y = pts[:, 0], pts[:, 1]
    M = np.stack([x * x, x * y, y * y, x, y], 1); c = np.linalg.lstsq(M, np.ones(len(x)), rcond=None)[0]
    A, Bq, C, D, E = c; den = 4 * A * C - Bq * Bq; x0 = (Bq * E - 2 * C * D) / den; y0 = (Bq * D - 2 * A * E) / den
    th = 0.5 * math.atan2(Bq, A - C)
    F = 1 + A * x0 * x0 + Bq * x0 * y0 + C * y0 * y0 - 0 + 0
    # semi-axes via rotated frame
    ct, st = math.cos(th), math.sin(th)
    Ap = A * ct * ct + Bq * ct * st + C * st * st; Cp = A * st * st - Bq * ct * st + C * ct * ct
    K = 1 - (A * x0 * x0 + Bq * x0 * y0 + C * y0 * y0 + D * x0 + E * y0) + (A * x0 * x0 + Bq * x0 * y0 + C * y0 * y0)
    K = 1 + (A * x0 * x0 + Bq * x0 * y0 + C * y0 * y0)
    ax1, ax2 = math.sqrt(K / Ap), math.sqrt(K / Cp)
    def er(b):  # ellipse radius from origin along bearing b
        a = math.radians(b); d = np.array([math.sin(a), math.cos(a)])
        p = np.array([x0, y0]); qa = A * d[0] ** 2 + Bq * d[0] * d[1] + C * d[1] ** 2
        qb = 2 * A * p[0] * d[0] + Bq * (p[0] * d[1] + p[1] * d[0]) + 2 * C * p[1] * d[1] + D * d[0] + E * d[1]
        qc = A * p[0] ** 2 + Bq * p[0] * p[1] + C * p[1] ** 2 + D * p[0] + E * p[1] - 1
        t = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa); return float(np.linalg.norm(p + t * d))
    return x0, y0, ax1, ax2, th, er
keep = out
for it in range(3):  # drop points >3 m off the fit (roof shadow, pitch marks), refit
    x0, y0, ax1, ax2, th, er = fit(keep)
    keep = [[b, r] for b, r in out if r and abs(r - er(b)) <= 3.0]
res = [(b, r, er(b), (r - er(b)) if r else None) for b, r in out]
print('ellipse centre %.1f %.1f semi %.1f %.1f rot %.1f deg' % (x0, y0, ax1, ax2, math.degrees(th)))
bad = [(b, r, round(e, 1), round(d, 1)) for b, r, e, d in res if d is None or abs(d) > 1.5]
print('off-ellipse >1.5 m:', bad)
json.dump(dict(trace=out, ell=[x0, y0, ax1, ax2, math.degrees(th)], er=[[b, round(e, 2)] for b, r, e, d in res]), open(os.path.join(SP, 'work', 'fence.json'), 'w'))
# Fence radius used by the build: the trace where it sits within 3 m of the fit (the real fence is not a true ellipse),
# the fit where the trace caught roof shadow or pitch marks; then a 15-degree circular median and 11-degree mean.
raw = np.array([r if (r and abs(r - er(b)) <= 3.0) else er(b) for b, r in out])
med = np.array([np.median(np.take(raw, range(i - 7, i + 8), mode='wrap')) for i in range(360)])
fr = np.array([np.mean(np.take(med, range(i - 5, i + 6), mode='wrap')) for i in range(360)])
J = json.load(open(os.path.join(SP, 'work', 'fence.json'))); J['fr'] = [round(float(v), 2) for v in fr]
json.dump(J, open(os.path.join(SP, 'work', 'fence.json'), 'w'))
print('fr min %.1f max %.1f' % (fr.min(), fr.max()))
