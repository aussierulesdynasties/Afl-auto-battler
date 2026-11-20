"""Fit the camera of photo B (Sweet Lime 2024) to the model built from photo A:
roof silhouettes (white roofs segmented in B) + two tower tops. Output camB.json."""
import numpy as np, json, math, os, sys
from PIL import Image, ImageDraw
from scipy.optimize import minimize
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def R(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
def proj(p, X):
    X = np.atleast_2d(X); d = (X - p[:3]) @ R(*p[3:6]).T
    return np.stack([p[7] + p[6] * d[:, 0] / d[:, 2], p[8] - p[6] * d[:, 1] / d[:, 2]], 1), d[:, 2]

def ply(fn):
    L = open(fn).read().split('\n'); nv = int([l for l in L if l.startswith('element vertex')][0].split()[-1])
    nf = int([l for l in L if l.startswith('element face')][0].split()[-1]); h = L.index('end_header') + 1
    V = np.array([list(map(float, l.split()[:3])) for l in L[h:h + nv]])
    F = [list(map(int, l.split()[1:])) for l in L[h + nv:h + nv + nf]]
    return V, F
W, H = 1950, 1301; S = 4  # mask downscale
ph = np.asarray(Image.open(os.path.join(ROOT, 'photos/sweetlime_2024.jpg')).convert('RGB')).astype(int)
mn, mx = ph.min(2), ph.max(2)
white = (mn > 175) & (mx - mn < 45)
region = np.zeros_like(white); region[700:1045, 0:640] = True
PM = (white & region)[::S, ::S]
REG = region[::S, ::S]
tris = []
for n in ('roof_east', 'roof_west', 'roof_river'):
    V, F = ply(os.path.join(ROOT, 'model', n + '.ply'))
    # top surface only: first half of faces (underside follows)
    k = len([f for f in F if len(f) == 3]) // 2
    tris.append(V[np.array([f for f in F if len(f) == 3][:k])])
TRI = np.concatenate(tris)
TW = {t[0]: t[1:] for t in json.load(open(os.path.join(ROOT, 'osm/geo.json')))['towers']}
Ht = json.load(open(os.path.join(ROOT, 'cam.json')))['H']
TOPS = {9961520695: (527, 829), int(sys.argv[1]) if len(sys.argv) > 1 else 9961520698: (398, 681)}

def mask(p):
    P, z = proj(p, TRI.reshape(-1, 3)); P = P.reshape(-1, 3, 2) / S; z = z.reshape(-1, 3)
    im = Image.new('L', (W // S + 1, H // S + 1), 0); d = ImageDraw.Draw(im)
    for t, zz in zip(P, z):
        if (zz > 1).all(): d.polygon([tuple(q) for q in t], fill=1)
    return np.asarray(im)[:PM.shape[0], :PM.shape[1]].astype(bool) & REG
def loss(p, verbose=False):
    m = mask(p); iou = (m & PM).sum() / max(1, (m | PM).sum())
    e = [np.linalg.norm(proj(p, np.array([[*TW[k], Ht]]))[0][0] - np.array(v)) for k, v in TOPS.items()]
    if verbose: print('iou', round(iou, 3), 'tower px', np.round(e, 1))
    return (1 - iou) + 0.003 * np.mean(e)
def lookat(C, T):
    f = (T - C) / np.linalg.norm(T - C); return math.atan2(f[1], f[0]), math.asin(f[2])
if __name__ == '__main__':
    T = np.array([-10.0, -30.0, 20.0]); best = None
    for az in range(150, 250, 10):
        for el in (15, 22, 30, 38, 46):
            for dist in (350, 500, 700, 950):
                for fo in (1500, 2200, 3200):
                    a, e = math.radians(az), math.radians(el)
                    C = T + dist * np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
                    yw, pt = lookat(C, T); p = np.r_[C, yw, pt, 0.0, fo, W / 2, H / 2]
                    l = loss(p)
                    if best is None or l < best[0]: best = (l, p)
    print('grid best', round(best[0], 3), np.round(best[1], 2))
    q0 = best[1][:7]
    f = lambda q: loss(np.r_[q, W / 2, H / 2])
    r = minimize(f, q0, method='Powell', options={'maxiter': 6000, 'xtol': 1e-3, 'ftol': 1e-5})
    p = np.r_[r.x, W / 2, H / 2]; loss(p, True)
    json.dump({'p': list(p), 'H': Ht, 'tops': {str(k): v for k, v in TOPS.items()}}, open(os.path.join(ROOT, 'camB_%s.json' % (sys.argv[1] if len(sys.argv) > 1 else 'x')), 'w'))
    print('C', np.round(p[:3]), 'f', round(p[6]))
