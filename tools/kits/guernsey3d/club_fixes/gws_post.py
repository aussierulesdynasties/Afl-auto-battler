# GWS front after the trace: the straightened photo's blurred outline left light-grey specks along the shoulders and
# sides that the trace read as the G's white. The G is the only white on the guernsey: white above the yoke's lower
# edge becomes orange, and white specks away from the G (pieces under 3000 px) take the colour round them.
import numpy as np
from PIL import Image
from scipy import ndimage as nd
p = 'design_GWS_front.png'
a = np.array(Image.open(p)).astype(int)
O, C, W = np.array([0xE9, 0x5E, 0x1B]), np.array([0x12, 0x1D, 0x1F]), np.array([0xCD, 0xD0, 0xD5])
on = a[..., 3] > 0
d = lambda c: np.abs(a[..., :3] - c).sum(-1)
white = on & (d(W) < d(O)) & (d(W) < d(C))
yoke = np.argmax((d(C) < 60)[:, 1000])  # first charcoal row at the centre
lab, n = nd.label(white)
sz = nd.sum(white, lab, range(1, n + 1))
bad = white & ((np.arange(a.shape[0])[:, None] < yoke) | np.isin(lab, [i + 1 for i, s in enumerate(sz) if s < 3000]))
_, (iy, ix) = nd.distance_transform_edt(bad | ~on, return_indices=True)
a[..., :3][bad] = a[..., :3][iy[bad], ix[bad]]
Image.fromarray(a.astype(np.uint8)).save(p)
print('GWS front: yoke edge row', yoke, 'white specks recoloured', int(bad.sum()))
