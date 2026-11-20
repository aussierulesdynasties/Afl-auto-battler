"""Fit one roof's shape to its white area in photo A and photo B at once.
usage: roofit.py NAME  (regions in REG below). Writes spec_fit_<name>.json params and prints IoUs."""
import numpy as np, json, math, os, sys
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.optimize import minimize
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
name = sys.argv[1]
_argv = sys.argv; sys.argv = ['gen.py']
src = open('tools/gen.py').read().split('# ---------------------------------------------------------------- build')[0]
__file__ = os.path.join(ROOT, 'tools', 'gen.py'); exec(src); sys.argv = _argv
def R(yaw, pt, roll):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pt), math.sin(pt), math.cos(roll), math.sin(roll)
    f = np.array([cy * cp, sy * cp, sp]); r = np.array([sy, -cy, 0.0]); u = np.cross(r, f)
    return np.array([cr * r + sr * u, -sr * r + cr * u, f])
def proj(p, X):
    d = (X - p[:3]) @ R(*p[3:6]).T
    return np.stack([p[7] + p[6] * d[:, 0] / d[:, 2], p[8] - p[6] * d[:, 1] / d[:, 2]], 1)
REG = {'river': {'A': (815, 520, 1400, 700), 'B': (395, 730, 615, 890)}}[name]
CAMS = {'A': (np.array(json.load(open('cam.json'))['p']), 'photos/crop.jpg'),
        'B': (np.array(json.load(open('camB.json'))['p']), 'photos/sweetlime_2024.jpg')}
def clean(m):
    m = ndimage.binary_opening(m, iterations=2); lab, n = ndimage.label(m)
    if n: m = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
    return ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3))
PM = {}
for k, (p, f) in CAMS.items():
    b = REG[k]; a = np.asarray(Image.open(f).convert('RGB')).astype(int)[b[1]:b[3], b[0]:b[2]]
    mn, mx = a.min(2), a.max(2); PM[k] = clean((mn > 150) & (mx - mn < 70))
rf = {r['name']: r for r in SPEC['roofs']}[name]
P0 = way(rf['way'])
def roof_xyz(q):
    dx, dy, sc, hf, hb, t1, z1, dome = q
    cen = P0[:-1].mean(0); P = (P0 - cen) * sc + cen + [dx, dy]
    V, T = fill(P, 2.0)
    a = (np.arctan2(P[:, 1] - PC[1], P[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi; a0, a1 = a.min(), a.max()
    d = seg_dist(V, PITCH); t = np.clip((d - rf['d0']) / (rf['d1'] - rf['d0']), 0, 1)
    ang = (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
    s = np.clip((ang - a0) / (a1 - a0), 0, 1)
    z = hf + (hb - hf) * np.interp(t, [0, min(max(t1, 0.05), 0.95), 1], [0, z1, 1]) - dome * (2 * s - 1) ** 2
    return np.c_[V, z], T
def mask(k, X, T):
    p = CAMS[k][0]; b = REG[k]; U = proj(p, X) - b[:2]
    im = Image.new('L', (b[2] - b[0], b[3] - b[1]), 0); dr = ImageDraw.Draw(im)
    for t in T: dr.polygon([tuple(U[i]) for i in t], fill=1)
    return np.asarray(im).astype(bool)
def loss(q, v=False):
    X, T = roof_xyz(q); L = 0
    for k in CAMS:
        m = mask(k, X, T); iou = (m & PM[k]).sum() / max(1, (m | PM[k]).sum()); L += 1 - iou
        if v: print(k, 'IoU', round(iou, 3))
    return L
q0 = np.array([0, 0, 1.0, rf['hf'], rf['hb'], 0.6, 1.6, 0.0])
if name == 'river' and rf.get('tprof'): q0[5], q0[6] = rf['tprof'][1]
loss(q0, True)
r = minimize(loss, q0, method='Powell', options={'maxiter': 3, 'xtol': 1e-3, 'ftol': 1e-5})
print('fit', np.round(r.x, 3)); loss(r.x, True)
json.dump({'q': list(r.x)}, open('fit_%s.json' % name, 'w'))
X, T = roof_xyz(r.x)
for k in CAMS:
    b = REG[k]; ph = np.asarray(Image.open(CAMS[k][1]).convert('RGB'))[b[1]:b[3], b[0]:b[2]].copy()
    m = mask(k, X, T); e = m ^ ndimage.binary_erosion(m); pe = PM[k] ^ ndimage.binary_erosion(PM[k])
    ph[pe] = [255, 255, 0]; ph[e] = [0, 255, 255]
    Image.fromarray(ph).resize((ph.shape[1] * 2, ph.shape[0] * 2)).save('grid/fit_%s_%s.png' % (name, k))
