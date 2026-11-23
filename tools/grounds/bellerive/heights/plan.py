"""Plan the 5-point roof height pass: per house within 450 m, register its footprint on the Google Earth shot
(shift up to 3 m that best puts its outline on the roof's edge), then the ridge centre, the two ends on the axis
and the two sides, each 1.0 m in from the (shifted) walls."""
import json, math, os, sys, numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import houses_ge as H
W = os.environ['BELLERIVE_WORK']   # holds gate/tiles (ge_trees.py plan + shots) and hgt/
urls = json.load(open(W + '/gate/tiles/urls.json')); C = np.array(json.load(open(W + '/gate/tiles/centres.json')))
shots, grads = {}, {}
def grad(i):
    if i not in grads:
        im = np.asarray(Image.open(W + '/gate/tiles/ge/t%02d.png' % i).convert('L')).astype(float)
        g = ndimage.gaussian_filter(im, 0.8)
        grads[i] = np.hypot(ndimage.sobel(g, 1), ndimage.sobel(g, 0))
    return grads[i]
def boundary(q, n=60):
    out = []
    for k in range(len(q)):
        a, b = np.array(q[k]), np.array(q[(k + 1) % len(q)])
        L = np.linalg.norm(b - a); m = max(2, int(L))
        out += [a + (b - a) * t for t in np.linspace(0, 1, m, endpoint=False)]
    return np.array(out)
plan, pts_all = {}, {}
for h, pts in H.buildings(np.fromfile(H.OUT + '/buildings.bin', '<f4')):
    c = pts.mean(0)
    if h >= 0 or math.hypot(*c) > 450: continue
    for i in np.argsort((C[:, 0] - c[0]) ** 2 + (C[:, 1] + c[1]) ** 2)[:4]:
        ce, cn = C[i]
        q = np.array([(640 + (x - ce) * H.K, 360 + (z + cn) * H.K) for x, z in pts])
        if q[:, 0].min() < 12 or q[:, 1].min() < 12 or q[:, 0].max() > 1268 or q[:, 1].max() > 708: continue
        if q[:, 1].min() < 70 and q[:, 0].max() > 650 and q[:, 0].min() < 1130: continue
        break
    else:
        continue
    i = int(i); g = grad(i); bd = boundary(q)
    best, bs = -1, (0, 0)
    for dx in np.arange(-6, 6.5, 1.0):          # half-metre steps, up to 3 m
        for dy in np.arange(-6, 6.5, 1.0):
            p = bd + [dx, dy]
            v = g[np.clip(p[:, 1].astype(int), 0, 719), np.clip(p[:, 0].astype(int), 0, 1279)].mean()
            if v > best: best, bs = v, (dx, dy)
    sh = np.array(bs) / H.K                     # metres: (east, south)
    P = pts + sh
    e = [P[(j + 1) % len(P)] - P[j] for j in range(len(P))]
    ax = e[int(np.argmax([np.hypot(*d) for d in e]))]; ax = ax / np.hypot(*ax); ac = np.array([-ax[1], ax[0]])
    pc = P.mean(0); pu, pv = (P - pc) @ ax, (P - pc) @ ac
    # the ridge line: the middle of the across extent; the centre point: the pole of inaccessibility
    x0, z0 = P.min(0) - 1; s = 4
    m = Image.new('L', (int((P[:, 0].max() - x0 + 1) * s) + 1, int((P[:, 1].max() - z0 + 1) * s) + 1))
    ImageDraw.Draw(m).polygon([((x - x0) * s, (z - z0) * s) for x, z in P], fill=1)
    d = ndimage.distance_transform_edt(np.asarray(m)); r, cc = np.unravel_index(np.argmax(d), d.shape)
    cen = np.array([x0 + cc / s, z0 + r / s])
    vm = (pv.max() + pv.min()) / 2
    pts5 = {'c': cen,
            'e1': pc + ax * (pu.max() - 1.0) + ac * vm, 'e2': pc + ax * (pu.min() + 1.0) + ac * vm,
            's1': cen + ac * ((pv.max() - 1.0) - (cen - pc) @ ac), 's2': cen + ac * ((pv.min() + 1.0) - (cen - pc) @ ac)}
    name = H.key(pts).replace(',', '_').replace('-', 'm')
    for k, (x, z) in pts5.items():
        plan.setdefault(i, []).append([name + '__' + k, round(640 + (x - ce) * H.K, 1), round(360 + (z + cn) * H.K + 140, 1)])
    pts_all[name] = {'key': H.key(pts), 'shift': [round(float(v), 2) for v in sh], 'pts': {k: [round(float(a), 2) for a in v] for k, v in pts5.items()},
                     'L': round(float(pu.max() - pu.min()), 2), 'W': round(float(pv.max() - pv.min()), 2)}
json.dump([[urls[i][1], p] for i, p in sorted(plan.items())], open(W + '/hgt/plan5.json', 'w'))
json.dump(pts_all, open(W + '/hgt/points5.json', 'w'))
print(len(pts_all), 'houses,', sum(len(p) for p in plan.values()), 'points,', len(plan), 'views')
sh = np.array([v['shift'] for v in pts_all.values()]); print('median shift m', np.median(sh, 0), 'median |shift|', np.median(np.hypot(*sh.T)))
