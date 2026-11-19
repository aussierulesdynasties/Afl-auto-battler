# gcs_front_edge.py (run after norm2, before trace): the straightened three-quarter front has ragged sides and
# shoulders where unwarp2 had to rebuild what the camera could not see. The front takes the straight back photo's
# outline (front and back meet at the shoulder and side seams): cloth outside it goes white, the neck lining seen
# through the V stays, and any other pale gap inside it takes the colour of the nearest cloth in its row.
import numpy as np
from PIL import Image
from scipy import ndimage as nd
f = np.asarray(Image.open('ref/GCS_front.png').convert('RGB')).copy()
b = np.asarray(Image.open('ref/GCS_back.png').convert('RGB'))
bc = nd.binary_fill_holes(b.astype(int).sum(2) < 735)   # the back's white sponsor letters are cloth too
pale = f.astype(int).min(2) > 150
lab, _ = nd.label(pale[:300]); lin = np.zeros_like(pale); lin[:300] = lab == lab[100, 1000]
out = np.full_like(f, 255)
for y in range(2000):
    xs = np.nonzero(bc[y])[0]
    if not len(xs): continue
    good = ~pale[y] | lin[y]
    gx = np.nonzero(good & bc[y])[0]
    if not len(gx): continue
    for x in xs:
        out[y, x] = f[y, x] if good[x] else f[y, gx[np.argmin(np.abs(gx - x))]]
Image.fromarray(out).save('ref/GCS_front.png')
