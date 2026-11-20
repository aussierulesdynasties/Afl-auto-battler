"""camera C fit: towers (bearing+collar), roof valleys (bearing), and the lawn outline draped from Esri vs the photo lawn."""
import numpy as np, json, math, sys, os
sys.path.insert(0, 'tools')
from esri import m2px, px2m
from PIL import Image
from scipy.optimize import minimize
from scipy import ndimage
Z = float(os.environ.get('EYE', '1.6'))
def g(px, py, h): return px2m(px - 0.82 * h, py - 0.26 * h)
SE = np.array([105.29, -75.82]); NE = np.array([65.65, 112.08])
T = json.load(open('spec.json'))['towers']; zc = T['kink'] - T['collar']
pts = [(SE, zc, 490, 285), (NE, zc, 3425, 716),
       (g(1311, 1311, 30), 0, 1150, None), (g(1327, 1171, 30), 0, 1940, None), (g(1289.5, 996, 30), 0, 2750, None)]
ph = np.asarray(Image.open('close/east_gate_2023.jpg').convert('RGB')).astype(int)
M = np.asarray(Image.open('esri/mosaic.jpg').convert('RGB')).astype(int)
s = 8; H, W = 2160 // s, 3840 // s
P = np.asarray(Image.fromarray(ph.astype(np.uint8)).resize((W, H))).astype(int)
U, V = np.meshgrid(np.arange(W) * s + s / 2, np.arange(H) * s + s / 2)
def green(a): return (a[..., 1] > a[..., 0] + 12) & (a[..., 1] > a[..., 2] + 12)
PL = green(P) & (V > 1390)
PL = ndimage.binary_opening(PL, iterations=1)
EX = (U > 720) & (U < 2200) & (V > 1416) & (V < 1920)   # cycad planter: green but not lawn
ROI = (V > 1390) & ~EX
MG = green(M); MG = ndimage.binary_opening(MG, iterations=2)
a0 = np.array(m2px(0, 0)); ax = np.array(m2px(1, 0)) - a0; ay = np.array(m2px(0, 1)) - a0
def drape(q):
    x0, y0, yaw, f, cy = q
    th = (U - 1920) / f; tv = (V - cy) / f; ok = tv > 0.004
    rho = np.where(ok, Z / np.maximum(tv, 1e-6), 0); rho = np.minimum(rho, 300)
    fx, fy = math.cos(yaw), math.sin(yaw); rx, ry = math.sin(yaw), -math.cos(yaw)
    gx = x0 + rho * (np.cos(th) * fx + np.sin(th) * rx); gy = y0 + rho * (np.cos(th) * fy + np.sin(th) * ry)
    px = a0[0] + gx * ax[0] + gy * ay[0]; py = a0[1] + gx * ax[1] + gy * ay[1]
    inb = ok & (px >= 0) & (py >= 0) & (px < M.shape[1] - 1) & (py < M.shape[0] - 1)
    G = np.zeros((H, W), bool); G[inb] = MG[py[inb].astype(int), px[inb].astype(int)]
    return G
def proj(q, X):
    x0, y0, yaw, f, cy = q
    d = np.array(X, float) - [x0, y0, Z]; fx, fy = math.cos(yaw), math.sin(yaw); rx, ry = math.sin(yaw), -math.cos(yaw)
    dz = d[:, 0] * fx + d[:, 1] * fy; dx = d[:, 0] * rx + d[:, 1] * ry; rho = np.hypot(dx, dz)
    return np.stack([1920 + f * np.arctan2(dx, dz), cy - f * d[:, 2] / rho], 1)
X = [[p[0][0], p[0][1], p[1]] for p in pts]
WG = float(os.environ.get('WG', '3'))
def loss(q, v=False):
    t = proj(q, X); r = []
    for (Pp, z, u, vv), tt in zip(pts, t):
        r.append(tt[0] - u)
        if vv is not None: r.append(tt[1] - vv)
    r = np.array(r); G = drape(q) & ROI; L = PL & ROI
    iou = (G & L).sum() / max(1, (G | L).sum())
    if v: print('res', np.round(r), 'lawn IoU', round(iou, 3))
    return np.mean((r / 30) ** 2) + WG * (1 - iou) + ((q[4] - 1360) / 30) ** 2 * 0.1
q0 = np.array(json.load(open('camC4.json'))['p'])
loss(q0, True)
best = None
for dx in (-15, 0, 15):
    for dy in (-15, 0, 15):
        q = q0 + [dx, dy, 0, 0, 0]
        r = minimize(loss, q, method='Powell', options={'xtol': 1e-3, 'ftol': 1e-6, 'maxiter': 3000})
        if best is None or r.fun < best.fun: best = r
q = best.x; print('C', np.round(q[:2], 1), 'yaw', round(math.degrees(q[2]), 2), 'f', round(q[3]), 'cy', round(q[4])); loss(q, True)
json.dump({'p': list(map(float, q)), 'model': 'cyl', 'eye': Z}, open('camC7.json', 'w'))
