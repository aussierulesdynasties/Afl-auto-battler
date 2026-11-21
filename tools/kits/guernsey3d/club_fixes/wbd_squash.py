# wbd_squash.py: Western Bulldogs, run last on the designs (after trace, wbd_design_fix.py).
# The AFL Store photo of the Bulldogs guernsey stands about 10 cm taller above the armpit than every other
# club's: placed by its armpit and chest width, its top reaches row 10 of the frame where Hawthorn's and
# Melbourne's reach row 246-247. Cut that way the neck sat 6 cm up the neck (neck loop to 1.674 m against
# 1.603-1.613 m for the other clubs) and the collar binding broke into red patches over the back.
# Director 2026-11-19, asked to lower it or drop the binding: "Lower to other clubs".
# Rows 10-520 of each design are squashed into rows 246-520 (x0.537, straight line, every column); rows from
# 520 down stay as they are, so the front F.F.C. (rows 572-656) and the hoops keep their shape. The back's
# F.F.C. (rows 85-163, under the collar) is put back unsquashed, centred where its middle row lands.
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
TOP0, TOP1, KEEP = 10.0, 246.0, 520.0
k = (KEEP - TOP1) / (KEEP - TOP0)
for side in ('front', 'back'):
    p = f'design_WBD_{side}.png'
    a = np.asarray(Image.open(p).convert('RGBA')).astype(np.float32)
    H, W = a.shape[:2]
    yo = np.arange(H, dtype=np.float32)
    ys = np.where(yo >= KEEP, yo, np.where(yo >= TOP1, KEEP - (KEEP - yo) / k, -10.0))
    Y, X = np.meshgrid(ys, np.arange(W, dtype=np.float32), indexing='ij')
    out = np.stack([map_coordinates(a[..., c], [Y, X], order=0, mode='constant', cval=0.0) for c in range(4)], -1)
    if side == 'back':
        y0, y1, x0, x1 = 85, 164, 915, 1101
        patch = a[y0:y1, x0:x1]
        mid = KEEP - (KEEP - (y0 + y1) / 2) * k
        t = int(round(mid - (y1 - y0) / 2))
        out[t:t + (y1 - y0), x0:x1] = patch
        print('back F.F.C. pasted at rows', t, t + y1 - y0)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(p)
    r = np.nonzero(out[..., 3].max(1) > 127)[0]
    print(side, 'rows', r.min(), '-', r.max())
# The front's sides. The front photo's mannequin is turned, so its left side shows the side panel (half-width
# 571 px at row 420 against 438 on the right; the director's straight-on back is 455 both sides). Where front
# and back sides disagree, the cut's armhole loop jogs at the side seam and the armhole binding draws ragged red
# down the side. Rows 246-1000: the front's outermost left and right edges are set to the back's (mirrored, as the
# back is seen from behind); the front's own neck opening between them is kept; cloth added at an edge takes the
# colour of the front's own last cloth pixel on that row.
f = np.asarray(Image.open('design_WBD_front.png').convert('RGBA')).copy()
b = np.asarray(Image.open('design_WBD_back.png').convert('RGBA'))[:, ::-1]
for y in range(246, 1001):
    fx = np.nonzero(f[y, :, 3] > 127)[0]; bx = np.nonzero(b[y, :, 3] > 127)[0]
    if not len(fx) or not len(bx):
        continue
    l0, r0, l1, r1 = fx.min(), fx.max(), bx.min(), bx.max()
    left, right = f[y, l0].copy(), f[y, r0].copy()
    f[y, :l1, 3] = 0; f[y, r1 + 1:, 3] = 0
    if l1 < l0: f[y, l1:l0] = left
    if r1 > r0: f[y, r0 + 1:r1 + 1] = right
Image.fromarray(f).save('design_WBD_front.png')
print('front sides set to the back\'s on rows 246-1000')
