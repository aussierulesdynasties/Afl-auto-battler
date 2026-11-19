# wbd_sides.py: Western Bulldogs front, run after wbd_armhole.py.
# The front photo's mannequin is turned, so below the armpit its outer columns carry the side panel at an angle:
# a red block under the hoop on the left, the hoop cut off at row 998 on the right, white flecks, and a see-through
# hole (rows 1001-1650, columns ~1385-1440). At the side seam the front's hoop also sat 19 rows above the back's.
# Rows 840 down, columns left of 620 and right of 1350: every pixel inside the row's outline is cloth, and each column
# is redrawn from the clean column next to it (620 / 1350), its colour bands moved in a straight line so that at the
# outline they meet the back's bands at the seam (hoop top 927, hoop bottom 1069, white top 1118, white bottom 1257).
import numpy as np
from PIL import Image
p = 'design_WBD_front.png'
f = np.asarray(Image.open(p).convert('RGBA')).copy()
# Step 1. From row 1000 down the front photo hangs turned and loose: shifted ~30 px left and flaring to 463-1446 at
# the hem, where the straight-on back keeps ~585-1414. Each front row from 1000 down is stretched sideways (nearest
# pixel) so its outline lands on the back's mirrored outline; below row 1700, where the back's hem curves up, the
# row-1700 stretch carries on, so the front keeps its own hem shape.
bm = (np.asarray(Image.open('design_WBD_back.png').convert('RGBA'))[..., 3] > 127)[:, ::-1]
g = f.copy()
YK = 1700
def lr(a, y):
    xs = np.nonzero(a[y])[0]
    return (xs.min(), xs.max()) if len(xs) else None
fa = f[..., 3] > 127
lk, rk = lr(fa, YK); blk, brk = lr(bm, YK)
sk = (brk - blk) / (rk - lk)
for y in range(1000, f.shape[0]):
    fe = lr(fa, y)
    if fe is None: continue
    if y <= YK and lr(bm, y) is not None:
        (l0, r0), (l1, r1) = fe, lr(bm, y)
    else:
        l0, r0 = fe; l1, r1 = blk + (l0 - lk) * sk, blk + (r0 - lk) * sk
    xo = np.arange(f.shape[1])
    xs = l0 + (xo - l1) * (r0 - l0) / max(1.0, (r1 - l1))
    inside = (xo >= l1) & (xo <= r1)
    row = np.zeros_like(f[y]); row[inside] = f[y, np.clip(np.round(xs[inside]).astype(int), l0, r0)]
    g[y] = row
f = g
src = f.copy()
BACK = np.array([927.0, 1069.0, 1118.0, 1257.0])
def bounds(x):
    c = src[:, x].astype(int); out = []; prev = None
    for y in range(840, 1400):
        r, g, b = c[y, :3]
        k = 'R' if r > 180 and b < 120 else 'W' if r > 180 and b > 180 else 'B'
        if prev is not None and k != prev: out.append(y)
        prev = k
    return np.array(out[:4], float)
H = f.shape[0]
alpha = f[..., 3] > 127
rows = np.arange(840, H)
L = np.full(H, -1); R = np.full(H, -1)
for y in rows:
    xs = np.nonzero(alpha[y])[0]
    if len(xs): L[y], R[y] = xs.min(), xs.max()
for ref, xs in ((620, range(int(L[840:].clip(0).min()) if (L[840:] >= 0).any() else 620, 620)), (1350, range(1351, int(R[840:].max()) + 1))):
    rb = bounds(ref)
    print('ref', ref, rb)
    for x in xs:
        for y in rows:
            if L[y] < 0 or x < L[y] or x > R[y]: continue
            edge = L[y] if ref == 620 else R[y]   # this row's own outline, so the bands meet the back's at the seam
            t = min(1.0, abs(x - ref) / max(1, abs(edge - ref)))
            tb = rb * (1 - t) + BACK * t
            kx = np.concatenate([[840.0], tb, [H - 1.0]]); ky = np.concatenate([[840.0], rb, [H - 1.0]])
            sy = int(round(np.interp(y, kx, ky)))
            f[y, x, :3] = src[sy, ref, :3]; f[y, x, 3] = 255
Image.fromarray(f).save(p)
print('front edge columns redrawn')
