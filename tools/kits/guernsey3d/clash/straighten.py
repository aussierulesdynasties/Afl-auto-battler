"""Straighten a three-quarter shop photo (unwarp2.py's ellipse model, with the cloth found as norm_clash does,
so a white guernsey isn't lost to the white behind it): each row's cloth is an ellipse (depth/width 0.65)
turned by theta, every output column is read from where that point lands in the photo.

    python straighten.py SRC DST Y0 Y1 [THETA_DEG]

Theta is fitted so the stripes between rows Y0 and Y1 (equal on the garment) come out equal width.
DST is a cut-out (alpha = the cloth), ready for warp_clash.py."""
import sys, os, numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from norm_clash import flat, cloth

src, dst, Y0, Y1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
a, alpha = flat(src)
m = cloth(a, alpha)
H, W, _ = a.shape
K = 0.65
X0 = W // 2


def warp_row(y, th, out, om):
    z = np.nonzero(m[y])[0]
    if len(z) < 5:
        return
    L, R = z.min(), z.max()
    c, hw = (L + R) / 2, (R - L) / 2
    A = hw / np.sqrt(np.cos(th) ** 2 + K * K * np.sin(th) ** 2)
    B = K * A
    xo = np.arange(int(X0 - A), int(X0 + A) + 1)
    xo = xo[(xo >= 0) & (xo < W)]
    u = (xo - X0) / A
    ok = np.abs(u) <= 1
    xo, u = xo[ok], u[ok]
    t = np.arcsin(u)
    nx, nz = np.sin(t) / A, np.cos(t) / B
    vis = (-nx * np.sin(th) + nz * np.cos(th)) > 0
    t = np.where(vis, t, -t)
    xs = c + A * np.sin(t) * np.cos(th) - B * np.cos(t) * np.sin(th)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 2)
    fr = (xs - x0)[:, None]
    out[y, xo] = a[y, x0] * (1 - fr) + a[y, x0 + 1] * fr
    om[y, xo] = m[y, x0] | m[y, x0 + 1]


def stripe_cv(th):
    out = np.full((H, W, 3), 255, np.float32)
    om = np.zeros((H, W), bool)
    s = []
    for y in range(Y0, Y1, 10):
        warp_row(y, th, out, om)
        dark = out[y].sum(1) < 300
        d = np.nonzero(np.diff(dark.astype(int)))[0]
        runs = np.diff(d)[1:-1]
        if len(runs) > 2:
            s.append(np.std(runs) / np.mean(runs))
    return np.mean(s) if s else 9


if len(sys.argv) > 5:
    th = np.radians(float(sys.argv[5]))
else:
    cand = np.radians(np.arange(-40, 41, 1.0))
    sc = [stripe_cv(t) for t in cand]
    th = cand[int(np.argmin(sc))]
    print('fit theta %.0f cv %.3f (cv at 0: %.3f)' % (np.degrees(th), min(sc), sc[40]))
out = np.full((H, W, 3), 255, np.float32)
om = np.zeros((H, W), bool)
for y in range(H):
    warp_row(y, th, out, om)
Image.fromarray(np.dstack([out.clip(0, 255).astype(np.uint8), (om * 255).astype(np.uint8)])).save(dst)
print('wrote', dst)
