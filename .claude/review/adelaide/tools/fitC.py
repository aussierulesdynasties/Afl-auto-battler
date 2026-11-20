"""Camera C (close/east_gate_2023.jpg) from the skyline: model roofs+stands silhouette top vs the photo's sky edge.
Works at 960x540 (1/4). Writes camC.json with p at full res (3840x2160)."""
import numpy as np, json, math, os, sys
from PIL import Image, ImageDraw
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(__file__))
from fitB import R, proj, ply
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 960, 540
top = np.load(os.path.join(ROOT, 'grid/C_sky.npy')).astype(float)
valid = np.zeros(W, bool); valid[50:890] = True
for a, b in ((100, 150), (335, 380), (840, 875)): valid[a:b] = False
CACHE = os.path.join(ROOT, 'grid/C_tri.npy')
tris = [np.load(CACHE)] if os.path.exists(CACHE) else []
for n in [] if tris else ('roof_east', 'roof_west', 'roof_river', 'stands'):
    V, F = ply(os.path.join(ROOT, 'model', n + '.ply'))
    T = [f for f in F if len(f) == 3]; Q = [f for f in F if len(f) == 4]
    T += [[q[0], q[1], q[2]] for q in Q] + [[q[0], q[2], q[3]] for q in Q]
    tris.append(V[np.array(T)])
TRI = np.concatenate(tris)
if not os.path.exists(CACHE): np.save(CACHE, TRI)
def topline(p):
    P, z = proj(p, TRI.reshape(-1, 3)); P = P.reshape(-1, 3, 2); z = z.reshape(-1, 3)
    ok = (z > 1).all(1) & (P[:, :, 0].max(1) > 0) & (P[:, :, 0].min(1) < W) & (P[:, :, 1].min(1) < H)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for t in P[ok]: d.polygon([tuple(q) for q in t], fill=1)
    m = np.asarray(im).astype(bool); has = m.any(0)
    return np.where(has, np.argmax(m, 0), H).astype(float)
def loss(p, verbose=False):
    t = topline(p); e = np.clip(np.abs(t - top)[valid], 0, 40)
    if verbose: print('mean px', round(e.mean(), 2), 'median', np.median(e))
    return e.mean()
if __name__ == '__main__':
    best = None
    for Cx in (150, 165, 180, 200):
        for Cy in (-30, -15, 0, 15):
            for yaw in (170, 180, 190):
                for f in (300, 375, 450, 550):
                    for cy in (300, 340, 370):
                        p = np.r_[Cx, Cy, 1.6, math.radians(yaw), 0.0, 0.0, f, W / 2, cy]
                        l = loss(p)
                        if best is None or l < best[0]: best = (l, p)
    print('grid', round(best[0], 2), np.round(best[1], 2))
    fx = lambda q: loss(np.r_[q[:7], W / 2, q[7]])
    q0 = np.r_[best[1][:7], best[1][8]]
    r = minimize(fx, q0, method='Powell', options={'maxiter': 8000, 'xtol': 1e-3, 'ftol': 1e-4})
    p = np.r_[r.x[:7], W / 2, r.x[7]]; loss(p, True)
    pf = p.copy(); pf[6:] *= 4
    json.dump({'p': list(pf), 'W': 3840, 'Himg': 2160}, open(os.path.join(ROOT, 'camC.json'), 'w'))
    print('C', np.round(p[:3], 1), 'yaw', round(math.degrees(p[3]), 1), 'pitch', round(math.degrees(p[4]), 1), 'roll', round(math.degrees(p[5]), 1), 'f', round(p[6] * 4), 'cy', round(p[8] * 4))
