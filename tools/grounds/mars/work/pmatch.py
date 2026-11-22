# Solve a camera for press/aus_new.jpg from marked points, then draw the model's key lines over the photo.
# Unknowns: eye x,y,z, heading, tilt, fovy, front height of the new roofs at their ends (he) and mid-span of new_s (hm).
import json, math, numpy as np
from PIL import Image, ImageDraw
fr = json.load(open('work/fence.json'))['fr']; FR = np.array(fr + [fr[0]])
J = json.load(open('model/mars.json', encoding='utf-8')); S = {s['name']: s for s in J['stands']}
def fence_r(b): return float(np.interp(b % 360, np.arange(361), FR))
def interp(t, b): t = np.array(t); return np.interp(b, t[:, 0], t[:, 1]), np.interp(b, t[:, 0], t[:, 2])
def P(b, r, z): a = math.radians(b); return np.array([r * math.sin(a), r * math.cos(a), z])
W, H = 1200, 675
def cam(p):
    x, y, z, h, t, fov = p[:6]; hr, tr = math.radians(h), math.radians(t)
    fwd = np.array([math.sin(hr) * math.sin(tr), math.cos(hr) * math.sin(tr), -math.cos(tr)])
    rt = np.array([math.cos(hr), -math.sin(hr), 0.0]); up = np.cross(rt, fwd); f = (H / 2) / math.tan(math.radians(fov) / 2)
    return np.array([x, y, z]), fwd, rt, up, f
def proj(p, X):
    C, fw, rt, up, f = cam(p); d = X - C; zz = d @ fw
    return np.array([W / 2 + f * (d @ rt) / zz, H / 2 - f * (d @ up) / zz])
def roofz(s, b, u, he, hm):   # front lip height: ends he, middle hm (arch), u=0 front
    b0, b1 = s['b0'], s['b1']; t = (b - b0) / (b1 - b0); return he + (hm - he) * (1 - (2 * t - 1) ** 2)
OBS = [('se', 142, (742, 368)), ('s', 146, (690, 412)), ('s', 188, (1150, 410)), ('s', 167, (930, 352))]
FEN = [(150, 522), (160, 522), (170, 521), (180, 520)]
def top(p, st, b, dz=None):   # highest projected point of the model's roof surface at bearing b (the silhouette seen from below)
    ri, ro = interp(st['roof'], b); z0, z1 = st['z_roof']; t = (b - st['b0']) / (st['b1'] - st['b0']); lift = -st['arch'] * (2 * t - 1) ** 2 + (OFF.get(st['name'], 0.0) if dz is None else dz)
    q = [proj(p, P(b, ri + (ro - ri) * u, z0 + (z1 - z0) * u + st['camber'] * 4 * u * (1 - u) + lift)) for u in np.linspace(0, 1, 9)]
    return min(q, key=lambda v: v[1])
OFF = {}
def pdist(pt, poly):
    A, B = poly[:-1], poly[1:]; d = B - A; t = np.clip(((pt - A) * d).sum(1) / np.maximum((d * d).sum(1), 1e-9), 0, 1)
    return np.min(np.linalg.norm(A + d * t[:, None] - pt, axis=1))
FENPTS = [(20, 563), (270, 548), (380, 541), (600, 527), (1000, 522), (1190, 520)]
LIP = {'new_se': [(20, 222), (110, 200), (240, 182), (450, 207), (600, 268), (700, 330), (740, 366)], 'new_s': [(752, 383), (930, 352), (1100, 380), (1148, 406)]}
def res(p):
    he, hmR = p[6], p[7]; r = []
    fpoly = np.array([proj(p, P(b, fence_r(b), 0.0)) for b in np.arange(40, 240, 1.0)])
    if not np.all(np.isfinite(fpoly)): return np.full(20, 1e4)
    for pt in FENPTS: r.append(pdist(np.array(pt, float), fpoly))
    OFF['new_se'] = p[6] - 14.5; OFF['new_s'] = p[7] - 17.5
    for nm, pts in LIP.items():
        st = S[nm]; hm = hmR if nm == 'new_s' else p[8]
        poly = np.array([top(p, st, b) for b in np.linspace(st['b0'], st['b1'], 60)])
        for pt in pts: r.append(pdist(np.array(pt, float), poly))
    C = cam(p)[0]
    for nm in ('new_se', 'new_s'):   # eye must see the lip from in front (z of view ray positive)
        pass
    r.append(0.3 * (p[6] - 14.5)); r.append(0.3 * (p[7] - 17.5))
    bb = math.degrees(math.atan2(p[0], p[1])); r.append(5 * max(0, math.hypot(p[0], p[1]) - fence_r(bb) + 3))
    r.append(10 * (p[2] - 1.7)); 
    return np.array(r)
def lm(p, n=40):
    for it in range(n):
        r0 = res(p); Jm = np.zeros((len(r0), len(p)))
        for k in range(len(p)):
            dp = np.zeros(len(p)); dp[k] = 1e-3; Jm[:, k] = (res(p + dp) - r0) / 1e-3
        st = np.linalg.lstsq(Jm.T @ Jm + 1.0 * np.eye(len(p)), -Jm.T @ r0, rcond=None)[0]
        st = np.clip(st, -5, 5); q = p + st
        if np.sum(res(q) ** 2) < np.sum(r0 ** 2): p = q
    return p
rng = np.random.default_rng(1); best = None
for k in range(20):
    p0 = np.array([rng.uniform(-20, 60), rng.uniform(-30, 60), 1.6, rng.uniform(160, 230), rng.uniform(88, 98), rng.uniform(30, 70), rng.uniform(12, 17), rng.uniform(15, 21), rng.uniform(15, 22)])
    try:
        q = lm(p0, 15); e = np.sum(res(q) ** 2)
    except Exception: continue
    if np.isfinite(e) and (best is None or e < best[0]): best = (e, q)
p = lm(best[1], 40)
print('params', np.round(p, 2)); print('resid', np.round(res(p), 1))
json.dump(list(p), open('work/p1cam.json', 'w'))
im = Image.open('press/aus_new.jpg').convert('RGB'); d = ImageDraw.Draw(im)
def line(pts, c): 
    q = [tuple(proj(p, X)) for X in pts]; d.line(q, fill=c, width=2)
line([P(b, fence_r(b), 0) for b in np.arange(60, 230, 1)], (255, 0, 255))
for nm in ('new_se', 'new_s'):
    s = S[nm]; bs = np.linspace(s['b0'], s['b1'], 40); hm = p[7] if nm == 'new_s' else p[8]
    d.line([tuple(top(p, s, b)) for b in bs], fill=(255, 255, 0), width=2)
for xy in FENPTS + LIP['new_se'] + LIP['new_s']: d.ellipse([xy[0] - 4, xy[1] - 4, xy[0] + 4, xy[1] + 4], outline=(0, 255, 255), width=2)
im.save('render/pm_p1.jpg', quality=90)
