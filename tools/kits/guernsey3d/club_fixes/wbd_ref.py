# wbd_ref.py: Western Bulldogs. Photos: the AFL Store ghost-mannequin front and back (dl_wbd/s_0.jpg, s_1.jpg),
# one camera (same top and hem rows), normalised with FIT=1 norm2.py WBD 405 405 samecam.
# On both photos the mannequin is turned a touch, so through the right armhole you see the garment's pale inside
# lining and, past it, the other panel's red binding. Neither is this panel's cloth: right of this panel's binding
# goes to background. The edge: the lining's first pixel (r,g >150, b >200), read every 15 rows on the normalised
# photo; above the lining it runs straight up to the panel's shoulder tip, below it down to the armpit; between the
# points it is interpolated and smoothed (Gaussian, sigma 4 rows).
# Front: the Mission sponsor sits on plain blue right above the club's F.F.C. letters, too close for trace.py's
# padded box (its fill bridges up from the letters), so its area (x 958-1332, rows 330-577, ending 6 rows above
# F.F.C.) is painted the body's blue (0,53,156, median of the plain blue at 900,1500) before the trace.
# Back: the CoinSpot panel covers the hoops' middle (the end of the red hoop, the blue gap and most of the white).
# Both outer edges stay visible on every column: the red hoop's top above the panel and the white hoop's bottom below
# it. Each is read per column (x 560-1440) and fitted with a straight line (the back is turned a touch, so they slope
# about 30 px across). Where the red ends and the white starts, as a share of that height, is read just outside the
# panel on each side (x 596 and 1334) and interpolated across it (left 0.44/0.57, as on the front; the turned right
# side reads less), over x 600-1330.
# Run after norm2 (reads ref/WBD_<side>_photo.png, writes ref/WBD_<side>.png).
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
for side in ('front', 'back'):
    a = np.asarray(Image.open(f'ref/WBD_{side}_photo.png').convert('RGB')).copy()
    ai = a.astype(int)
    r, g, b = ai[..., 0], ai[..., 1], ai[..., 2]
    red = (r > 170) & (g < 110) & (b < 120)
    bg = ai.min(-1) > 245
    wh = (ai.min(-1) > 200) & ~bg
    E = {'front': [(180, 1496), (255, 1461), (270, 1456), (285, 1451), (300, 1446), (315, 1443), (330, 1441),
                   (345, 1436), (360, 1432), (375, 1430), (390, 1428), (405, 1426), (420, 1424), (435, 1422),
                   (450, 1421), (465, 1420), (480, 1419), (525, 1418), (570, 1419), (585, 1420), (600, 1421),
                   (615, 1422), (630, 1423), (645, 1424), (660, 1426), (675, 1429), (690, 1431), (735, 1440),
                   (765, 1448)],
         'back': [(195, 1530), (285, 1503), (300, 1499), (315, 1495), (330, 1491), (345, 1490), (360, 1486),
                  (375, 1484), (390, 1482), (405, 1480), (420, 1478), (435, 1477), (450, 1476), (465, 1475),
                  (480, 1474), (525, 1474), (540, 1473), (570, 1472), (585, 1471), (600, 1470), (615, 1468),
                  (630, 1467), (645, 1465), (660, 1463), (675, 1461), (705, 1461), (735, 1460), (765, 1455)]}[side]
    ys = np.arange(E[0][0], E[-1][0] + 1)
    e = gaussian_filter1d(np.interp(ys, [p[0] for p in E], [p[1] for p in E]), 4, mode='nearest')
    for y, x in zip(ys, np.rint(e).astype(int)):
        a[y, x:] = 255
    print(side, 'right armhole cut on rows', ys[0], '-', ys[-1])
    if side == 'front':
        a[330:578, 958:1333] = (0, 53, 156)
    else:
        xs, ts, ws = [], [], []
        for x in range(560, 1441, 4):
            rr = np.nonzero(red[850:960, x])[0]
            ww = np.nonzero(wh[1240:1330, x])[0]
            if len(rr) and len(ww) and not bg[1240 + ww.max() + 3, x]:
                xs.append(x); ts.append(850 + rr.min()); ws.append(1240 + ww.max() + 1)
        kt, ct = np.polyfit(xs, ts, 1); kw, cw = np.polyfit(xs, ws, 1)
        def frac(x):
            t = kt * x + ct; w = kw * x + cw
            col = red[round(t):round(w), x]; re = round(t) + np.nonzero(col)[0].max() + 1
            ws = re + np.nonzero(wh[re:round(w), x])[0].min()
            return (re - t) / (w - t), (ws - t) / (w - t)
        (fl1, fl2), (fr1, fr2) = frac(596), frac(1334)
        for x in range(600, 1331):
            t = kt * x + ct; w = kw * x + cw; u = (x - 596) / (1334 - 596)
            f1 = fl1 + (fr1 - fl1) * u; f2 = fl2 + (fr2 - fl2) * u
            r1, w0 = round(t + f1 * (w - t)), round(t + f2 * (w - t))
            a[round(t):r1, x] = (235, 7, 32); a[r1:w0, x] = (0, 53, 156); a[w0:round(w), x] = (235, 235, 246)
        print('band shares left %.3f/%.3f right %.3f/%.3f' % (fl1, fl2, fr1, fr2))
        print('back hoops: red top %.0f-%.0f, white bottom %.0f-%.0f (x 600-1330), %d columns read'
              % (kt * 600 + ct, kt * 1340 + ct, kw * 600 + cw, kw * 1340 + cw, len(xs)))
    Image.fromarray(a).save(f'ref/WBD_{side}.png')
