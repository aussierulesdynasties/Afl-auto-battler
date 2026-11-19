# The photo's blurred outline leaves specks of background-tinted colour a few pixels inside the
# traced cut edge (pale flecks on the cloth once the atlas padding stretches them past the edge).
# Within BAND px of the outline, a pixel whose 25 px neighbourhood is at least 70% one main colour
# takes that colour (a speck); where two colours genuinely meet (no 70% majority) it is left alone.
# python club_fixes/edge_specks.py CODE side [--dry]
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as nd
code, side = sys.argv[1:3]; dry = '--dry' in sys.argv
BAND, WIN, MAJ = 45, 41, 0.7
f = f'design_{code}_{side}.png'
src = f.replace('.png', '_pre_specks.png')
import os
a = np.array(Image.open(src if os.path.exists(src) else f).convert('RGBA'))
op = a[..., 3] > 250
rgb = a[..., :3].astype(int)
cols, cnt = np.unique(rgb[op], axis=0, return_counts=True)
main = cols[cnt > 0.01 * cnt.sum()]
lab = np.argmin(((rgb[..., None, :] - main[None, None]) ** 2).sum(-1), -1)
near = op & (nd.distance_transform_edt(op) < BAND)
opn = cv2.boxFilter(op.astype(np.float32), -1, (WIN, WIN), normalize=False)
share = np.stack([cv2.boxFilter((op & (lab == c)).astype(np.float32), -1, (WIN, WIN), normalize=False)
                  for c in range(len(main))], -1) / np.maximum(opn, 1)[..., None]
best = share.argmax(-1); top = share.max(-1)
fix = near & (top >= MAJ) & (np.abs(rgb - main[best]).max(-1) > 6)
print(f, 'main', [tuple(int(v) for v in m) for m in main], 'speck px', int(fix.sum()))
if dry:
    raise SystemExit
if not os.path.exists(src):
    Image.fromarray(a).save(src)
a[..., :3][fix] = main[best][fix].astype(np.uint8)
Image.fromarray(a).save(f)
