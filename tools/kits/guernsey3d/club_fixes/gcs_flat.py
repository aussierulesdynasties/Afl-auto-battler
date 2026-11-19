# gcs_flat.py (after norm2 and gcs_front_edge, before trace): GCS's sun and side lines are tonal (a lighter red on
# red), too close to the base for trace's colour snap under the photo's lighting. Each is found by its local contrast
# (a pixel lighter than the 25-61 px around it) and the refs are redrawn flat: base red, the lighter red for the sun
# and the side lines, the neck lining left as they are. Sponsors (VOAO, AFL, Hostplus, the jock
# tag, Zambrero, SIXT) are not part of any motif, so they fall to the base red.
# The side lines are clearest on the side turned away from the camera, which gcs_ref mirrors away: they are read from
# the straightened photo (dl_gcs/f_15nm.png) before the mirror, put in the frame with norm2's transform and drawn on
# both sides. The photos are kept as ref/GCS_*_photo.png for the board.
import json, shutil, numpy as np
from PIL import Image
from scipy import ndimage as nd
BASE, SUN = (235, 72, 54), (249, 82, 47)
xf = json.load(open('norm_GCS.json'))
def hp(a, w):
    g = a[:, :, 1] + 1.0
    return g / nd.uniform_filter(g, w)
for side in ('front', 'back'):
    shutil.copy(f'ref/GCS_{side}.png', f'ref/GCS_{side}_photo.png')
    a = np.asarray(Image.open(f'ref/GCS_{side}.png').convert('RGB')).astype(float)
    cloth = nd.binary_fill_holes(a.sum(2) < 735)
    pale = a.min(2) > 150
    out = np.full(a.shape, 255.0)
    out[cloth] = BASE
    if side == 'front':
        lab, _ = nd.label(pale[:300]); lin = np.zeros_like(pale); lin[:300] = lab == lab[100, 1000]
        out[lin] = a[lin]                                   # the neck lining seen through the V
        # The arc and the band under it (rows 712-905): their sides are about 130 px thick, so the contrast window is
        # 121 px. Each row is filled from the arc's outer edge (smoothed over 15 rows) to the edge of the opening
        # inside it. The four bars each side and the thin bottom arc (rows 905-1096) use a 61 px window.
        sun = np.zeros_like(cloth)
        arc = np.zeros_like(cloth); arc[712:905, 652:1349] = True
        arc &= hp(a, 121) > 1.03
        arc = nd.binary_opening(nd.binary_closing(arc, iterations=2), iterations=3)
        lab, n = nd.label(arc); sz = nd.sum(arc, lab, range(1, n + 1))
        arc = np.isin(lab, [i + 1 for i, v in enumerate(sz) if v > 3000])
        hl, hn = nd.label(~arc); hs = nd.sum(~arc, hl, range(1, hn + 1))
        inner = np.isin(hl, [i + 1 for i, v in enumerate(hs) if 20000 < v < 90000])
        rows = [y for y in range(712, 905) if arc[y, :1000].any()]
        Ls = nd.median_filter(np.array([np.nonzero(arc[y, :1000])[0].min() for y in rows]), 15)
        for y, L in zip(rows, Ls):
            ii = np.nonzero(inner[y, :1000])[0]
            sun[y, L:(ii.min() if len(ii) else 1000)] = True
        bars = np.zeros_like(cloth); bars[905:1096, 652:1349] = True
        bars &= hp(a, 61) > 1.04
        bars = nd.binary_opening(nd.binary_closing(bars, iterations=2), iterations=2)
        lab, n = nd.label(bars); sz = nd.sum(bars, lab, range(1, n + 1))
        sun |= np.isin(lab, [i + 1 for i, v in enumerate(sz) if v > 800])
        sun[:, 1000:] = sun[:, :1000][:, ::-1]                       # the left half mirrored (the photo is symmetric)
        out[sun] = SUN
        f = np.asarray(Image.open('dl_gcs/f_15nm.png').convert('RGB')).astype(float)
        f = np.roll(f, 25, axis=1); f[:, :25] = 255
        ln = (hp(f, 25) > 1.06) & (f.sum(2) < 735)
        reg = np.zeros_like(ln); reg[520:860, 620:760] = True    # below the sun, clear of the jock tag (y 860+)
        ln &= reg
        lab, n = nd.label(ln); sl = nd.find_objects(lab)          # the lines are long and thin: folds and specks are not
        ln = np.isin(lab, [i + 1 for i, o in enumerate(sl) if o[0].stop - o[0].start >= 40 and (lab[o] == i + 1).sum() <= 4 * (o[0].stop - o[0].start)])
        s, sy, tx, ty = xf['front']
        yy, xx = np.nonzero(ln)
        m = np.zeros(cloth.shape, bool)
        for dx in np.linspace(0, s, int(np.ceil(s)) + 1)[:-1]:
            for dy in np.linspace(0, sy, int(np.ceil(sy)) + 1)[:-1]:
                X = np.clip((xx * s + tx + dx).astype(int), 0, 1999); Y = np.clip((yy * sy + ty + dy).astype(int), 0, 1999)
                m[Y, X] = True
        m |= m[:, ::-1]
        m &= cloth & ~sun
        out[m] = SUN
        np.save('gcs_lines_mask.npy', m)
    # the back is plain base: the collar flag is left off (director 2026-11-19: "remove from gcs")
    Image.fromarray(out.astype(np.uint8)).save(f'ref/GCS_{side}.png')
    print(side, 'cloth', cloth.sum())
