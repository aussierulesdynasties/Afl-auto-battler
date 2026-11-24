"""Adelaide clash, back: the navy band runs under the Hungry Jack's box, so the trace sees only its ends and
the '@' walk can't rebuild it. On the photo (ref/ADE_back.png, the cut's square) it is one straight-edged
shape: top edge (645,1183) to (1415,870), left end down to (648,1242), bottom edge to its point at
(1130,1332), then up to the right side seam at (1415,1160). Over the band's rows, repaint the navy and white cloth
white, then that shape, so the traced ends and the rebuilt middle are one edge.
    python ade_back_bands.py   (work folder, after trace_clash.py)"""
import numpy as np
from PIL import Image
from matplotlib.path import Path

fn = 'design_ADE_back.png'
a = np.array(Image.open(fn).convert('RGBA'))
WHITE = np.array([0xDC, 0xD5, 0xD9])
NAVY = np.array([0x24, 0x23, 0x2E])
X0, Y0, X1, Y1 = 0, 820, 2000, 1360           # the band's rows; red and orange cloth there stays as traced
NAVY_BAND = [(645, 1183), (1415, 870), (1600, 790), (1600, 1050), (1415, 1160), (1130, 1332), (648, 1242)]
yy, xx = np.mgrid[Y0:Y1, X0:X1]
box = a[Y0:Y1, X0:X1]
inside = box[..., 3] > 0
band = Path(NAVY_BAND).contains_points(np.c_[xx.ravel() + .5, yy.ravel() + .5]).reshape(xx.shape)
for keep in (np.array([0xB6, 0x26, 0x2F]), np.array([0xEA, 0x95, 0x39])):   # red, orange
    inside &= np.abs(box[..., :3].astype(int) - keep).sum(-1) > 90
box[inside, :3] = WHITE
box[inside & band, :3] = NAVY
Image.fromarray(a).save(fn)
print('ade back navy band rebuilt')
