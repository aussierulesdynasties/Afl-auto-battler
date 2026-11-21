# wbd_ref.py: Western Bulldogs.
# Front: the AFL Store ghost-mannequin photo (dl_wbd/s_0.jpg), normalised with FIT=1 norm2.py WBD 405 405 samecam.
# The mannequin is turned a touch, so through the right armhole you see the garment's pale inside lining and, past
# it, the other panel's red binding. Neither is this panel's cloth: right of this panel's binding goes to
# background. The edge: the lining's first pixel (r,g >150, b >200), read every 15 rows on the normalised photo;
# above the lining it runs straight up to the panel's shoulder tip, below it down to the armpit; between the points
# it is interpolated and smoothed (Gaussian, sigma 4 rows).
# The Mission sponsor sits on plain blue right above the club's F.F.C. letters, too close for trace.py's padded box
# (its fill bridges up from the letters), so its area (x 958-1332, rows 330-577, ending 6 rows above F.F.C.) is
# painted the body's blue (0,53,156, median of the plain blue at 900,1500) before the trace.
# Back: the director's straight-on photo, placed and recoloured by wbd_back_norm.py (no sponsor, no turn).
# Both sides: the hoops are clean bands on the real guernsey, but their edges in the photos ripple with the cloth's
# folds and a straight trace copies every ripple (director 2026-11-19: "sloppy line work"). So each hoop edge (red
# top, red bottom, white top, white bottom) is read per column and fitted with one smooth curve across the width
# (a parabola, refitted 4 times leaving out columns more than 2.5x the median miss, so shading at the side seams
# does not bend the ends), and the hoops are repainted as flat bands between the fitted edges, with the body blue
# 40 rows above and below, on every column between the first and last cloth column (only background joined to the
# image border is put back, so the photo's near-white sheen inside the hoops is painted over).
# Run after norm2 and wbd_back_norm.py (reads ref/WBD_<side>_photo.png, writes ref/WBD_<side>.png).
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, median_filter, label
for side in ('front', 'back'):
    a = np.asarray(Image.open(f'ref/WBD_{side}_photo.png').convert('RGB')).copy()
    if side == 'front':
        E = [(180, 1496), (255, 1461), (270, 1456), (285, 1451), (300, 1446), (315, 1443), (330, 1441),
             (345, 1436), (360, 1432), (375, 1430), (390, 1428), (405, 1426), (420, 1424), (435, 1422),
             (450, 1421), (465, 1420), (480, 1419), (525, 1418), (570, 1419), (585, 1420), (600, 1421),
             (615, 1422), (630, 1423), (645, 1424), (660, 1426), (675, 1429), (690, 1431), (735, 1440),
             (765, 1448)]
        ys = np.arange(E[0][0], E[-1][0] + 1)
        e = gaussian_filter1d(np.interp(ys, [p[0] for p in E], [p[1] for p in E]), 4, mode='nearest')
        for y, x in zip(ys, np.rint(e).astype(int)):
            a[y, x:] = 255
        print(side, 'right armhole cut on rows', ys[0], '-', ys[-1])
        a[330:578, 958:1333] = (0, 53, 156)
        # the red collar and armhole binding (all red above row 860; the red hoop starts at ~900) go blue: the csv's
        # collar and armhole trims (#E40A23) draw the binding on the mesh's own edges, front and back alike. Left in
        # the design, the binding is the cloth's outer edge, so fillcell's nearest-colour fill spread it over every
        # part of the mesh past the photo's outline (red side panels, ragged shoulders, a red wedge on the back).
        ai = a.astype(int); top = np.zeros(a.shape[:2], bool); top[:860] = True
        binding = top & (ai[..., 0] > 110) & (ai[..., 0] > 2 * ai[..., 1]) & (ai[..., 0] > 1.5 * ai[..., 2])
        a[binding] = (0, 53, 156)
        print(side, 'binding px painted blue', int(binding.sum()))
    ai = a.astype(int); r, g, b = ai[..., 0], ai[..., 1], ai[..., 2]
    red = (r > 170) & (g < 110) & (b < 120); bg = ai.min(-1) > 245; wh = (ai.min(-1) > 200) & ~bg
    cx, E4 = [], []
    for x in range(0, 2000):
        if bg[820:1350, x].mean() > 0.5:
            continue
        rr = np.nonzero(red[820:1350, x])[0]
        if not len(rr):
            continue
        t1 = 820 + rr.min(); r2 = 820 + rr.max() + 1
        ww = np.nonzero(wh[r2:1350, x])[0]
        if not len(ww):
            continue
        w1 = r2 + ww.min(); w2 = r2 + ww.max() + 1
        cx.append(x); E4.append((t1, r2, w1, w2))
    cx = np.array(cx); E4 = np.array(E4, float)
    def fit(y):
        keep = np.ones(len(cx), bool)
        for _ in range(4):
            c = np.polyfit(cx[keep], y[keep], 2); res = y - np.polyval(c, cx)
            keep = np.abs(res) < max(3.0, 2.5 * np.median(np.abs(res[keep])))
        return np.polyval(c, cx), keep.mean()
    fits = [fit(E4[:, k]) for k in range(4)]
    print(side, 'edge fit inliers', ' '.join('%.2f' % f[1] for f in fits))
    E4 = np.stack([f[0] for f in fits], 1)
    BL, RD, WT = (0, 53, 156), (235, 7, 32), (235, 235, 246)
    lab, _ = label(bg); outside = np.isin(lab, np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) & bg
    xs_all = np.arange(cx.min(), cx.max() + 1)
    E4 = np.stack([np.interp(xs_all, cx, E4[:, k]) for k in range(4)], 1); cx = xs_all
    for x, (t1, r2, w1, w2) in zip(cx, np.rint(E4).astype(int)):
        keep = outside[:, x].copy()
        a[t1 - 40:t1, x] = BL; a[t1:r2, x] = RD; a[r2:w1, x] = BL; a[w1:w2, x] = WT; a[w2:w2 + 40, x] = BL
        a[keep, x] = 255
    print(side, 'hoops repainted on', len(cx), 'columns')
    Image.fromarray(a).save(f'ref/WBD_{side}.png')
