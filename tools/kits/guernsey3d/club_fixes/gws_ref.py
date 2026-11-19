# gws_ref.py: GWS has only three-quarter shots (jerseys.com.au). Front: straightened with unwarp2 at 9 deg (the collar's
# centre sat 24 px left of the outline's centre); the shoulders and orange yoke (rows above 355, plain orange apart from
# sponsors) take the left half mirrored onto the right, the G below is kept as photographed (it is not symmetric), and
# the yoke's lower edge, which the camera bends down to the right, is laid level on row 364 (its row at the centre).
# Back: straightened at 8 deg (collar 20 px left of the outline centre) and the near (left) half mirrored (unwarp2 L).
import numpy as np
from PIL import Image
a = np.asarray(Image.open('dl_gws/f_9.png').convert('RGB')).copy()
X0 = a.shape[1] // 2
for d in range(1, X0):
    a[:355, X0 + d] = a[:355, X0 - d]
cloth = a.astype(int).sum(2) < 735
for x in range(a.shape[1]):
    if not cloth[400, x]:
        continue
    org, dark = a[340, x].copy(), a[398, x].copy()
    if org[0] - org[2] < 90:
        continue  # the armhole binding columns: leave as photographed
    a[340:364, x] = org
    a[364:398, x] = dark
# above the collar the straightening leaves a thin spike of the back's collar (rows where the cloth is a sliver): white
for y in range(60):
    z = np.nonzero(cloth[y])[0]
    if len(z) and z.max() - z.min() < 150:
        a[y] = 255
Image.fromarray(a).save('ref_raw/GWS_front.png')
Image.open('dl_gws/b_8.png').convert('RGB').save('ref_raw/GWS_back.png')
print('GWS refs written')
