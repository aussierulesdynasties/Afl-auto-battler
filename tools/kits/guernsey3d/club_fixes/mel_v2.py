# Melbourne front, after the shoulder press: the red V's edge drawn as the photo's straight line
# (y = 771 + 0.97 (x - 925), measured either side of the AFL logos, mirrored about x 999.5) the whole
# way, from the armhole to one point at the centre. mel_v.py drew it only under the logos, leaving the
# trace's own edge at the ends: a nub at the armhole and a double point at the tip. Rows above the
# armpit were pressed afterwards (press_traced.py, k in mel_shoulder.json), so the line is pressed too.
import json, numpy as np
from scipy import ndimage as nd
from PIL import Image
A = 189.0 + (1.62 - 1.37) * 2310
k = json.load(open('mel_shoulder.json'))['front']
p = 'design_MEL_front.png'
a = np.array(Image.open(p)).astype(float)
RED, NAVY = np.array([0xEB, 0x10, 0x23]), np.array([0x19, 0x31, 0x6E])
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(float)
xl = np.minimum(xx, 1999 - xx)               # the left half's line, mirrored on the right
L = 771 + 0.97 * (xl - 925)                    # the line in unpressed rows
Lp = np.where(L < A, A - (A - L) * k, L)       # where it lies now
band = (np.abs(yy - Lp) < 26) & (a[..., 3] > 0) & (yy > 300)
t = np.clip(Lp - yy + 0.5, 0, 1)[..., None]   # 1 above the line (red)
# the red armhole binding (38 px wide in the design, 1.65 cm) runs over the V's ends: kept red
WB = 38.0
dist = nd.distance_transform_edt(a[..., 3] > 0)
t = np.maximum(t, np.clip(WB - dist + 0.5, 0, 1)[..., None])
a[..., :3] = np.where(band[..., None], t * RED + (1 - t) * NAVY, a[..., :3])
Image.fromarray(np.clip(a, 0, 255).round().astype(np.uint8)).save(p)
print('MEL V redrawn, tip row %.1f' % (771 + 0.97 * (999.5 - 925)), 'band px', band.sum())
