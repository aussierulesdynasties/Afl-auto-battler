# wbd_armhole.py: Western Bulldogs, run after wbd_squash.py.
# The store mannequin fills the armholes, so both photos show the red armhole binding edge-on and the traced sides run
# straight down from the shoulder (widest at row ~670) with no armhole scoop. The photos' binding ends at the armpit
# at row ~760, which is where our body's armpit is (frame row 766) and where every club whose photo shows an open
# armhole has its armpit corner. Cut from the straight sides, the armhole loop climbed across the front and the
# armhole binding drew ragged red ~8 cm down the side.
# Rows 340-760: the outermost left/right cloth edges are set to Hawthorn's (front to HAW front, back to HAW back;
# Hawthorn's binding draws clean on the same body). Rows 760-840 blend from Hawthorn's edges into WBD's own.
# Rows above 340 (shoulder tops and neck) are only clipped to Hawthorn's outline, never added to. Inside the edges
# nothing changes; cloth added at an edge takes the colour of the row's own last cloth pixel.
import numpy as np
from PIL import Image
R0, R1, R2 = 340, 760, 840
for side in ('front', 'back'):
    p = f'design_WBD_{side}.png'
    w = np.asarray(Image.open(p).convert('RGBA')).copy()
    h = np.asarray(Image.open(f'design_HAW_{side}.png').convert('RGBA'))[..., 3] > 127
    for y in range(246, R2):
        wx = np.nonzero(w[y, :, 3] > 127)[0]; hx = np.nonzero(h[y])[0]
        if not len(wx) or not len(hx):
            continue
        l0, r0 = wx.min(), wx.max()
        t = 0.0 if y < R1 else (y - R1) / (R2 - R1)
        l1 = int(round(hx.min() * (1 - t) + l0 * t)); r1 = int(round(hx.max() * (1 - t) + r0 * t))
        left, right = w[y, l0].copy(), w[y, r0].copy()
        w[y, :l1, 3] = 0; w[y, r1 + 1:, 3] = 0
        if y >= R0:
            if l1 < l0: w[y, l1:l0] = left
            if r1 > r0: w[y, r0 + 1:r1 + 1] = right
    Image.fromarray(w).save(p)
    a = w[..., 3] > 127
    print(side, ' '.join(f'{y}:{np.nonzero(a[y])[0].min()}-{np.nonzero(a[y])[0].max()}' for y in range(300, 900, 40)))
