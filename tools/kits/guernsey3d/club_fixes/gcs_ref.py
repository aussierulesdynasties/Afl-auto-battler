# gcs_ref.py: GCS has no straight-on front photo. Front: the AFL Store three-quarter shot straightened with unwarp2
# (15 deg, no mirror), moved so the garment's centre (the top of the sun logo's arc, 25 px left of the outline's
# centre) sits on the middle column, and its left half (the half facing the camera) mirrored onto the right.
# Back: the Jerseys Megastore back shot, which is nearly straight. Its grey background goes white, the outline's
# centre goes to the middle column, the left half (the clean armhole) is mirrored onto the right, and the collar's
# blue-and-gold flag is put back unmirrored on the centre.
import numpy as np
from PIL import Image
a = np.asarray(Image.open('dl_gcs/f_15nm.png').convert('RGB')).copy()
a = np.roll(a, 25, axis=1); a[:, :25] = 255
X0 = a.shape[1] // 2
for d in range(1, X0): a[:, X0 + d] = a[:, X0 - d]
Image.fromarray(a).save('ref_raw/GCS_front.png')

b = np.asarray(Image.open('dl_gcs/jm_b.jpg').convert('RGB')).astype(int)
g = (np.abs(b[:, :, 0] - b[:, :, 1]) < 14) & (np.abs(b[:, :, 1] - b[:, :, 2]) < 14) & (b.min(2) > 195)
b[g] = 255
o = np.full((1024, 1024, 3), 255, np.uint8); o[:, 216:216 + 591] = b
flag = o[6:27, 486:515].copy()                      # blue 488-500, gold 500-512, rows 8-26
red = (o[:, :, 0].astype(int) - o[:, :, 2]) > 80
cx = int(round(np.median([(lambda z: (z.min() + z.max()) / 2)(np.nonzero(red[r])[0]) for r in range(150, 900, 10)])))
o = np.roll(o, 512 - cx, axis=1)
for d in range(1, 512): o[:, 512 + d] = o[:, 512 - d]
o[6:27, 512 - 14:512 + 15] = flag
Image.fromarray(o).save('ref_raw/GCS_back.png')
print('back outline centre', cx)
