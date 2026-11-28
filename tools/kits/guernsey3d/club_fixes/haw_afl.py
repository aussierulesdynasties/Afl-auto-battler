# Hawthorn front: under the AFL logo (mirrored onto both sides by haw_front.py) the trace's box fill
# flattened two edges into a horizontal step: the gold wedge between the outer brown stripe and the
# next one (it rises to a point at row ~595 in the photo) and the brown stripe's right edge. Both are
# redrawn here from the photo: the wedge's two edges and the stripe edge are fitted to the photo's own
# boundary rows either side of the logo and drawn as those curves, mirrored on the right.
import numpy as np
from PIL import Image
ref = np.array(Image.open('ref/HAW_front.png').convert('RGB')).astype(float)
B, G = np.array([0x2E, 0x12, 0x0B], float), np.array([0xF5, 0xA9, 0x4E], float)
brown = ((ref - B) ** 2).sum(-1) < ((ref - G) ** 2).sum(-1)
def edges(y, x0, x1):
    r = brown[y, x0:x1]
    return [(i + x0, r[i]) for i in range(1, len(r)) if r[i] != r[i - 1]]
wl, wr, sr = [], [], []
for y in range(600, 736):
    t = edges(y, 560, 700)
    g = [x for x, b in t if not b]; b = [x for x, b in t if b]
    b = [x for x in b if g and x > g[0]]
    if g and b and b[0] - g[0] < 80:
        wl.append((y, g[0])); wr.append((y, b[0]))
for y in list(range(500, 586)) + list(range(700, 800)):
    t = edges(y, 700, 800)
    g = [x for x, b in t if not b]
    if g:
        sr.append((y, g[0]))
fit = lambda pts, d: np.polyfit([p[0] for p in pts], [p[1] for p in pts], d)
cl, cr, cs = fit(wl, 3), fit(wr, 3), fit(sr, 2)
for y in (600, 620, 640, 660, 700, 730):
    print(y, '%.1f %.1f' % (np.polyval(cl, y), np.polyval(cr, y)), [w for w in wl if w[0] == y], [w for w in wr if w[0] == y])
ys = np.arange(560, 400, -1)
tip = next(y for y in range(600, 500, -1) if np.polyval(cr, y) - np.polyval(cl, y) <= 0)
print('wedge tip row', tip, 'edges at 700:', np.polyval(cl, 700), np.polyval(cr, 700), 'stripe edge at 640:', np.polyval(cs, 640))
p = 'design_HAW_front.png'
d = np.array(Image.open(p)).astype(float)
# draw in the design's own two colours (the trace's palette), not the photo's
op = d[..., 3] == 255
cols_, cnt = np.unique(d[op][:, :3], axis=0, return_counts=True)
DB, DG = sorted(cols_[np.argsort(cnt)[-2:]], key=lambda c: c.sum())
print('design colours', DB, DG)
Y0, Y1, X0, X1 = 585, 741, 560, 800
yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(float)
for mirror in (False, True):
    x = xx  # the right side is the left mirrored: the same curves, placed at 1999 - x
    L, R, S = np.polyval(cl, yy), np.polyval(cr, yy), np.polyval(cs, yy)
    wedge = np.clip(x - L + 0.5, 0, 1) * np.clip(R - x + 0.5, 0, 1) * (yy > tip)
    gold = np.clip(wedge + np.clip(x - S + 0.5, 0, 1), 0, 1)[..., None]
    cols = slice(int(1999 - X1 + 1), int(1999 - X0 + 1)) if mirror else slice(X0, X1)
    blk = d[Y0:Y1, cols]
    g = gold[:, ::-1] if mirror else gold
    on = blk[..., 3:] > 0
    blk[..., :3] = np.where(on, g * DG + (1 - g) * DB, blk[..., :3])
Image.fromarray(np.clip(d, 0, 255).round().astype(np.uint8)).save(p)
print('HAW wedge and stripe edge redrawn under the AFL logos')
