# unwarp2.py SRC DST [THETA_DEG]: straighten a three-quarter back photo. Each row's cloth is taken as an
# ellipse (depth/width k) turned by theta; every output column is read from where that point of the ellipse
# lands in the photo, and points on the hidden side are mirrored from the seen side. With no THETA, theta is
# fitted so the bottom stripes (equal on the garment) come out equal width.
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
H, W, _ = a.shape; cloth = a.sum(2) < 735; K = 0.65; X0 = W // 2

YFIX = int(sys.argv[4]) if len(sys.argv) > 4 else H
def warp_row(y, th, out):
    z = np.nonzero(cloth[y])[0]
    if len(z) < 5: return
    L, R = z.min(), z.max()
    if y > YFIX:  # the hem curls away: keep the last straight row's width so stripes stay straight
        z2 = np.nonzero(cloth[YFIX])[0]; L, R = z2.min(), z2.max()
    c = (L + R) / 2; hw = (R - L) / 2
    A = hw / np.sqrt(np.cos(th) ** 2 + K * K * np.sin(th) ** 2); B = K * A
    xo = np.arange(int(X0 - A), int(X0 + A) + 1); u = (xo - X0) / A; ok = np.abs(u) <= 1
    xo, u = xo[ok], u[ok]; t = np.arcsin(u)
    nx, nz = np.sin(t) / A, np.cos(t) / B
    vis = (-nx * np.sin(th) + nz * np.cos(th)) > 0
    t = np.where(vis, t, -t)
    xs = c + A * np.sin(t) * np.cos(th) - B * np.cos(t) * np.sin(th) + B * np.sin(th) * 0
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 2); fr = (xs - x0)[:, None]
    out[y, xo] = a[y, x0] * (1 - fr) + a[y, x0 + 1] * fr

def stripe_std(th):
    out = np.full((H, W, 3), 255, np.float32); s = []
    for y in range(950, 1110, 20):
        warp_row(y, th, out)
        w = out[y].sum(1) > 560; d = np.nonzero(np.diff(w.astype(int)))[0]; runs = np.diff(d)
        runs = runs[1:-1]
        if len(runs) > 2: s.append(np.std(runs) / np.mean(runs))
    return np.mean(s) if s else 9

if len(sys.argv) > 3: th = np.radians(float(sys.argv[3]))
else:
    cand = np.radians(np.arange(-40, 41, 1.0)); sc = [stripe_std(t) for t in cand]
    th = cand[int(np.argmin(sc))]; print('fit theta', np.degrees(th), 'cv', min(sc), 'cv at 0', sc[40])
out = np.full((H, W, 3), 255, np.float32)
for y in range(H): warp_row(y, th, out)
if len(sys.argv) > 5:  # mirror the half that faces the camera (L or R) onto the other
    h = sys.argv[5]
    for d in range(1, X0):
        if h == 'L': out[:, X0 + d] = out[:, X0 - d]
        else: out[:, X0 - d] = out[:, X0 + d]
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst); print('wrote', dst)
