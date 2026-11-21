# wbd_binding.py: Western Bulldogs, run after wbd_sides.py.
# The red armhole binding is painted into the designs, as Hawthorn's and Sydney's are, and the csv armhole trim is
# blank. Drawn by the shader (armholes #E40A23 2.5) it broke into ragged red tongues down the back below each armpit
# (cap38), and with the trim off the same film was clean (cap39).
# Width copies Hawthorn's painted binding, which renders clean: 34 px in from the side outline (Hawthorn's back
# measures 30-35 px). Only the armhole edge gets it: from each side's shoulder corner (the first row from 280 down
# where the outline stops sloping in faster than 1 px per row) to the armpit (row 770), measured from the
# background left and right of the cloth on those rows, so the neck, the shoulder tops and the side seams below the
# armpit stay as they are. The band stops at the armpit corner (the side's outermost row between 650 and 770),
# so it does not run on below the armpit. Colour: the csv's armhole red #E40A23.
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
W, Y1 = 34, 770
RED = np.array([0xE4, 0x0A, 0x23], np.uint8)
for side in ('front', 'back'):
    p = f'design_WBD_{side}.png'
    a = np.asarray(Image.open(p).convert('RGBA')).copy()
    cloth = a[..., 3] > 127
    L = {y: np.nonzero(cloth[y])[0] for y in range(280, Y1 + 5)}
    def corner(k):
        for y in range(280, Y1):
            if len(L[y]) and len(L[y + 4]) and abs(int(k(L[y + 4])) - int(k(L[y]))) <= 4:
                return y
    band = np.zeros_like(cloth)
    for k in (np.min, np.max):
        y0 = corner(k)
        side_bg = np.zeros_like(cloth)
        for y in range(y0, Y1 + 1):
            if len(L[y]):
                if k is np.min: side_bg[y, :L[y].min()] = True
                else: side_bg[y, L[y].max() + 1:] = True
        d = distance_transform_edt(~side_bg)
        rr = [y for y in range(650, Y1 + 1) if len(L[y])]
        ya = rr[int(np.argmin([L[y].min() for y in rr]))] if k is np.min else rr[int(np.argmax([L[y].max() for y in rr]))]
        b = cloth & (d <= W); b[:y0] = False; b[ya + 1:] = False   # ends at the armpit corner (outermost row)
        print(side, 'armpit row', ya)
        if k is np.min: b[:, 1000:] = False
        else: b[:, :1000] = False
        band |= b
        print(side, 'left' if k is np.min else 'right', 'corner row', y0)
    a[band, :3] = RED
    Image.fromarray(a).save(p)
    print(side, 'binding px', int(band.sum()))
