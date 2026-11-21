# syd_ref.py: Sydney. Front: the AFL Store straight-on render (dl_syd/s_3.jpg), used as it is.
# Back: the only back photo is Nike's, turned about 16 deg and shot on a different mannequin (its length to width
# disagrees with the straight front by 14 cm at the hem), so as for Collingwood (col_back.py) the back is rebuilt in
# the straight front's frame and takes only its design from the photo:
#  - outline = the front's outline row by row (the back collar shows through the front's V; the V is filled)
#  - the back is plain red (the front's red), shoulder to hem
#  - the club's "SMFC" at the back of the neck is copied from the Nike back (straightened with unwarp2 at 16 deg,
#    dl_syd/back_u16.png, text centre x 1395, rows 212-263, 31 px below the back's top), scaled by the two photos'
#    chest widths (622 / 1588) and put on the centre line the same distance below the top.
# The house roundel and realestate.com.au on the Nike back are sponsors: not copied.
import numpy as np
from PIL import Image
exec(open('C:/kt/guernsey3d_work/measure.py').read().split('for c in sys.argv')[0])
f = np.asarray(Image.open('dl_syd/s_3.jpg').convert('RGB'))
Image.fromarray(f).save('ref_raw/SYD_front.png')
m = cloth('dl_syd/s_3.jpg')
RED = np.median(f[180:220, 300:340].reshape(-1, 3), 0).astype(np.uint8)
out = np.full(f.shape, 255, np.uint8)
rows = np.nonzero(m.any(1))[0]
# the white cloth's edge on the white studio ground is ragged row to row: each side's edge loses its outliers
# (median over 5 rows), then is smoothed (Gaussian, sigma 3 rows) so the armhole curves stay curves, not steps
from scipy.ndimage import median_filter, gaussian_filter1d
L = np.array([np.nonzero(m[y])[0].min() for y in rows]); R = np.array([np.nonzero(m[y])[0].max() for y in rows])
L = np.rint(gaussian_filter1d(median_filter(L, 5, mode='nearest').astype(float), 3, mode='nearest')).astype(int)
R = np.rint(gaussian_filter1d(median_filter(R, 5, mode='nearest').astype(float), 3, mode='nearest')).astype(int)
for y, l, r in zip(rows, L, R):
    out[y, l:r + 1] = RED
k = 622 / 1588
u = Image.open('dl_syd/back_u16.png').convert('RGB').crop((1395 - 135, 205, 1395 + 135, 272))
u = np.asarray(u.resize((round(270 * k), round(67 * k)), Image.LANCZOS)).astype(int)
txt = u.min(-1) > 150
z = np.nonzero(m[410])[0]; cx = (z.min() + z.max()) // 2
top = rows.min() + round((205 - 181) * k)
h, w = txt.shape
out[top:top + h, cx - w // 2:cx - w // 2 + w][txt] = (240, 240, 240)
Image.fromarray(out).save('ref_raw/SYD_back.png')
print('red', RED, 'centre', cx, 'SMFC at row', top, 'size', w, h)
