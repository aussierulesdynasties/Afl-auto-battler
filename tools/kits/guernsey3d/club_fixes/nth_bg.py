# North Melbourne: the shop renders sit on a flat light grey (244,244,244) with a soft drop shadow, not studio white,
# and the white upper back fades into that grey at its edges. Grey (242+) joined to the frame's edge is set to
# white; the renders are left-right symmetric about x 749.5, so on each row the side nearer the centre is the true
# edge (a shadow streak only ever widens one side) and both sides are cut to it. Below row 1220 the sides run straight
# (the shadow under the hem fans out both sides), so they keep that row's width; where the sides are blue, light
# pixels at a row's ends are shadow and are dropped. Between the armpit and row 1220 the side line is smoothed. Run before norm2.
import numpy as np
from PIL import Image
from scipy import ndimage as nd
C = 749.5
HEM0 = 1220
ARMPIT = {'front': 553, 'back': 558}
BLUE = {'front': (140, 1370), 'back': (1040, 1370)}  # rows where both side edges are blue
for side in ('front', 'back'):
    a = np.array(Image.open(f'ref_raw/old_nth/NTH_{side}.jpg').convert('RGB')).astype(int)
    g = (a.min(-1) >= 242) & (np.ptp(a, -1) <= 6)
    lab, _ = nd.label(g)
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    m = ~np.isin(lab, list(edge))
    lab, n = nd.label(m); s = nd.sum(m, lab, range(1, n + 1)); m = lab == (np.argmax(s) + 1)
    keep = np.zeros_like(m)
    xs = np.arange(m.shape[1]); H = np.zeros(m.shape[0])
    for r in np.nonzero(m.any(1))[0]:
        x = np.nonzero(m[r])[0]
        if BLUE[side][0] <= r < BLUE[side][1]:
            # the sides are blue here: light pixels at a row's ends are the shadow beside the cloth
            lit = a[r, :, :].min(-1) > 200
            while len(x) and lit[x[0]]: x = x[1:]
            while len(x) and lit[x[-1]]: x = x[:-1]
        h = min(C - x.min(), x.max() - C)
        if r == HEM0:
            hcap = h
        if r > HEM0:
            h = min(h, hcap)  # below this row the sides run straight to the hem; wider is the drop shadow
        H[r] = h
    # the side seams below the armpit are smooth lines: the photo's soft white edge leaves 2-10 px notches
    r0, r1 = ARMPIT[side] + 15, HEM0
    H[r0:r1] = nd.gaussian_filter1d(nd.median_filter(H[r0 - 20:r1 + 20], 21), 4)[20:-20]
    for r in np.nonzero(m.any(1))[0]:
        keep[r] = np.abs(xs - C) <= H[r]
    m &= keep
    m[r0:1370] = keep[r0:1370]  # body rows have no holes: where the white fades into the grey, the line decides
    a[m] = np.minimum(a[m], 240)  # the white cloth's lit edge (246+) would read as background to trace.py
    a[~m] = 255
    Image.fromarray(a.astype(np.uint8)).save(f'ref_raw/NTH_{side}.png')
    print('NTH', side, 'cloth px', m.sum())
