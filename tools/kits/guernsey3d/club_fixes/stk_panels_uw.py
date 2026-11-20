# St Kilda on the flat pattern (run after bake_unwrap.py, before stk_neck_uw.py:
#   python club_fixes/stk_panels_uw.py ATLAS CELL). Director 2026-11-20, "Yes, straight up": each front panel edge
#   (red|white, white|black) keeps its photographed chest position (median edge, 1.10-1.30 m) straight up from
#   1.40 m (above the emblem) to the shoulder seam; each panel's colour fills up to its line.
#   Only spots within 5 cm of a line change (the shoulder's white tab reaches 5 cm past it); the emblem keeps its own.
import sys, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ATLAS, CELL = sys.argv[1], int(sys.argv[2]); GX = 4
LO, NEAR = 1.40, 0.08
tx = np.load('texels_STK.npz'); ys, xs, p, f = tx['ys'], tx['xs'], tx['p'], tx['front']
at = np.array(Image.open(ATLAS).convert('RGB')); C = at.shape[1] // (GX * 2); row, col = divmod(CELL, GX)
cell = at[row*C:(row+1)*C, col*2*C:(col*2+2)*C]
c = cell[ys, xs].astype(float)
# the panels' own colours, measured on the chest (1.20-1.30 m)
chest = f & (p[:, 1] > 1.2) & (p[:, 1] < 1.3)
PAN = np.array([np.median(c[chest & (p[:, 0] > a) & (p[:, 0] < b)], 0) for a, b in ((-0.15, -0.06), (-0.02, 0.02), (0.1, 0.16))])
dist = np.linalg.norm(c[:, None, :] - PAN[None], axis=2); cls = dist.argmin(1); pure = dist.min(1) < 40
top = f & (p[:, 1] >= 1.10) & (p[:, 1] < 1.30) & pure
edges = []
for left, right, side in ((0, 1, -1), (1, 2, 1)):
    hs, xs_ = [], []
    for y in np.arange(1.10, 1.30, 0.005):
        r = top & (p[:, 1] >= y) & (p[:, 1] < y + 0.005) & (np.sign(p[:, 0]) == side) & (np.abs(p[:, 0]) < 0.2)
        a, b = r & (cls == left), r & (cls == right)
        if a.sum() < 3 or b.sum() < 3: continue
        # the edge in this row: the x that best splits the two panels (fewest spots on the wrong side)
        xa, xb = p[a, 0], p[b, 0]
        cand = np.sort(np.r_[xa, xb]); wrong = [(xa > t).sum() + (xb < t).sum() for t in cand]
        e = cand[int(np.argmin(wrong))]
        hs.append(y + 0.0025); xs_.append(e)
    k, m = 0.0, float(np.median(xs_))
    print('edge', ('red|white', 'white|black')[right - 1], 'chest rows', len(hs), 'x = %.4f' % m)
    edges.append((k, m))
(k1, m1), (k2, m2) = edges
x1 = k1 * p[:, 1] + m1; x2 = k2 * p[:, 1] + m2
want = np.where(p[:, 0] < x1, 0, np.where(p[:, 0] < x2, 1, 2))
near = (np.abs(p[:, 0] - x1) < NEAR) | (np.abs(p[:, 0] - x2) < NEAR)
# every spot near a line takes its panel's colour, the photo's blended edge pixels too (left alone they stood as
# slivers on the wrong side of the new line); the emblem's top (1.38-1.395 m, right of 5.5 cm) keeps its own
emblem = (p[:, 1] < 1.395) & (p[:, 0] > 0.055)
ch = f & (p[:, 1] >= LO) & near & ~emblem & ((want != cls) | ~pure)
cell[ys[ch], xs[ch]] = PAN[want[ch]].round().astype(np.uint8)
Image.fromarray(at).save(ATLAS)
print('panel-edge pattern pixels recoloured', int(ch.sum()))
