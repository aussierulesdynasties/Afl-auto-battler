"""Pieces of a traced design smaller than a size (a fleck of the photo's lining or binding left inside the
cloth, away from any edge) take the colour round them. Used by fixes/<code>_*_specks.py for the clubs whose
renders showed them; never run over a whole design blind, since a club's small marks (an anchor, a badge)
are pieces too."""
import numpy as np
from PIL import Image
from scipy import ndimage as nd


def despeckle(code, side, max_px, colours, box=None):
    fn = f'design_{code}_{side}.png'
    a = np.array(Image.open(fn).convert('RGBA'))
    cloth = a[..., 3] > 0
    rgb = a[..., :3].astype(int)
    fleck = np.zeros(cloth.shape, bool)
    for c in colours:
        c = np.array([int(c[k:k + 2], 16) for k in (1, 3, 5)])
        m = cloth & (np.abs(rgb - c).sum(-1) < 120)
        lab, n = nd.label(m)
        if n == 0:
            continue
        sizes = nd.sum(m, lab, range(1, n + 1))
        small = np.nonzero(sizes <= max_px)[0] + 1
        fleck |= np.isin(lab, small)
    if box:
        inb = np.zeros_like(fleck)
        inb[box[1]:box[3], box[0]:box[2]] = True
        fleck &= inb
    fleck = nd.binary_dilation(fleck, iterations=2) & cloth
    keep = cloth & ~fleck
    _, (iy, ix) = nd.distance_transform_edt(~keep, return_indices=True)
    a[fleck, :3] = a[iy[fleck], ix[fleck], :3]
    Image.fromarray(a).save(fn)
    return int(fleck.sum())
