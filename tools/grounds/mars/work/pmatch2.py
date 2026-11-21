# Solve a camera for press/bcc2.jpg (City of Ballarat, Oct 2025, field level) scaled to ge/p2.png 1200x900.
# Unknowns: eye x,y,z, heading, tilt, fovy, back-top height of new_se (hse) and new_s (hs).
import json, math, numpy as np
from PIL import Image, ImageDraw
fr = json.load(open('work/fence.json'))['fr']; FR = np.array(fr + [fr[0]])
J = json.load(open('model/mars.json', encoding='utf-8')); S = {s['name']: s for s in J['stands']}
def fence_r(b): return float(np.interp(b % 360, np.arange(361), FR))
def rout(s, b): t = np.array(s['roof']); return float(np.interp(b, t[:, 0], t[:, 2])) - s['back_in']
def P(b, r, z): a = math.radians(b); return np.array([r * math.sin(a), r * math.cos(a), z])
W, H = 1200, 900
def cam(p):
    x, y, z, h, t, fov = p[:6]; hr, tr = math.radians(h), math.radians(t)
    fwd = np.array([math.sin(hr) * math.sin(tr), math.cos(hr) * math.sin(tr), -math.cos(tr)])
    rt = np.array([math.cos(hr), -math.sin(hr), 0.0]); up = np.cross(rt, fwd); f = (H / 2) / math.tan(math.radians(fov) / 2)
    return np.array([x, y, z]), fwd, rt, up, f
def proj(p, X):
    C, fw, rt, up, f = cam(p); d = X - C; zz = d @ fw
    if zz <= 0.1: return np.array([1e5, 1e5])
    xn, yn = (d @ rt) / zz, (d @ up) / zz; rr = (xn * xn + yn * yn) * (f / (W / 2)) ** 2; k = 1 + K1[0] * rr
    return np.array([W / 2 + f * xn * k, H / 2 - f * yn * k])
def pdist(pt, poly):
    A, B = poly[:-1], poly[1:]; d = B - A; t = np.clip(((pt - A) * d).sum(1) / np.maximum((d * d).sum(1), 1e-9), 0, 1)
    return np.min(np.linalg.norm(A + d * t[:, None] - pt, axis=1))
FENPTS = [(150, 584), (300, 580), (500, 576), (750, 572), (900, 571), (1150, 569)]
SE, SS = S['new_se'], S['new_s']
TOPS = [(SE, 'se', SE['b0'], (305, 439)), (SE, 'se', SE['b1'], (642, 491)), (SS, 's', SS['b0'], (732, 499)), (SS, 's', SS['b1'], (1117, 512))]
USE_TOPS = True
K1 = [0.0]
EAST = [(10, 353), (80, 372), (150, 392), (225, 413), (300, 435)]
def res(p):
    r = []; K1[0] = p[8] if len(p) > 8 else 0.0
    fpoly = np.array([proj(p, P(b, fence_r(b), 0.0)) for b in np.arange(20, 260, 1.0)])
    for pt in FENPTS: r.append(pdist(np.array(pt, float), fpoly))
    for s, k, b, xy in (TOPS if USE_TOPS else []):
        z = p[6] if k == 'se' else p[7]; q = proj(p, P(b, rout(s, b), z)); r += list(q - np.array(xy))
    E = S['east']; lip = np.array([proj(p, P(b, float(np.interp(b, [t[0] for t in E['roof']], [t[1] for t in E['roof']])), E['z_roof'][0])) for b in np.arange(420, 458.1, 1.0)])
    for pt in EAST: r.append(2 * pdist(np.array(pt, float), lip))
    bb = math.degrees(math.atan2(p[0], p[1])); r.append(5 * max(0, math.hypot(p[0], p[1]) - fence_r(bb) + 3))
    r.append(30 * (p[2] - 1.6)); r.append(0.05 * (p[6] - 12)); r.append(0.05 * (p[7] - 12))
    return np.array(r)
def lm(p, n=40):
    for it in range(n):
        r0 = res(p); Jm = np.zeros((len(r0), len(p)))
        for k in range(len(p)):
            dp = np.zeros(len(p)); dp[k] = 1e-3; Jm[:, k] = (res(p + dp) - r0) / 1e-3
        st = np.linalg.lstsq(Jm.T @ Jm + 1.0 * np.eye(len(p)), -Jm.T @ r0, rcond=None)[0]
        q = p + np.clip(st, -5, 5)
        if np.sum(res(q) ** 2) < np.sum(r0 ** 2): p = q
    return p
rng = np.random.default_rng(2); best = None
for k in range(40):
    p0 = np.array([rng.uniform(-80, 20), rng.uniform(-60, 40), 1.6, rng.uniform(60, 140), rng.uniform(85, 95), rng.uniform(40, 70), rng.uniform(8, 16), rng.uniform(8, 16), rng.uniform(-0.3, 0.1)])
    q = lm(p0, 15); e = np.sum(res(q) ** 2)
    if np.isfinite(e) and (best is None or e < best[0]): best = (e, q)
p = lm(best[1], 60)
print('params', np.round(p, 2)); print('resid', np.round(res(p), 1))
json.dump(list(p), open('work/p2cam.json', 'w'))
im = Image.open('ge/p2.png').convert('RGB'); d = ImageDraw.Draw(im)
d.line([tuple(proj(p, P(b, fence_r(b), 0))) for b in np.arange(30, 240, 1)], fill=(255, 0, 255), width=2)
for s, z in ((SE, p[6]), (SS, p[7])):
    bs = np.linspace(s['b0'], s['b1'], 30); d.line([tuple(proj(p, P(b, rout(s, b), z))) for b in bs], fill=(255, 255, 0), width=2)
for xy in FENPTS + [t[3] for t in TOPS]: d.ellipse([xy[0] - 4, xy[1] - 4, xy[0] + 4, xy[1] + 4], outline=(0, 255, 255), width=2)
im.save('render/pm_p2.jpg', quality=90)

# measure: bearing and height where each observed stand corner ray meets the stand's back radius
C, fw, rt, up, f = cam(p)
for s_, k, b, (u, v) in TOPS:
    ray = fw + rt * (u - W / 2) / f + up * (H / 2 - v) / f
    best = None
    for bb in np.arange(s_['b0'] - 15, s_['b1'] + 15, 0.1):
        ro = rout(s_, min(max(bb, s_['b0']), s_['b1'])); a = math.radians(bb)
        # point on ray whose horizontal pos is at bearing bb: solve x/y ratio
        dx, dy = ray[0], ray[1]; sx, sy = math.sin(a), math.cos(a)
        den = dx * sy - dy * sx
        if abs(den) < 1e-9: continue
        tt = (sx * C[1] - sy * C[0]) / den; X = C + tt * ray
        if tt <= 0: continue
        err = abs(math.hypot(X[0], X[1]) - ro)
        if err < 3 and (best is None or err < best[0]): best = (err, bb, X[2])
    if best is None: print(k, 'no hit'); continue
    print(k, 'model b', b, '-> photo b %.1f z %.1f (fit err %.1f m)' % (best[1], best[2], best[0]))
