# wbd_back_norm.py: Western Bulldogs back, from the director's photo (2026-11-19, "perhaps a better back view / beware
# the creases but its cleaner than what youre working with"; dl_wbd/director_back.png, 1000x1000, straight on, no sponsor).
# It is a different camera from the AFL Store front, so norm2's chest rule would put its hem 5 cm below the front's
# (and push the front off the frame). The AFL Store front and back come from one camera and show the back's top,
# armpit and hem rows (frame rows 5, 766.5, 1901 from FIT=1 norm2.py WBD 405 405 samecam); this photo is placed on
# those three rows (top-armpit and armpit-hem each stretched evenly), and across to the chest width (905 px at the
# armpit, as norm2). Writes ref/WBD_back_photo.png (wbd_ref.py then makes ref/WBD_back.png).
# Raw rows read on a pixel grid: top 81 (back collar), armpit 362 (side seam turns straight down), hem 950 (centre).
import numpy as np
from PIL import Image
exec(open('C:/kt/guernsey3d_work/measure.py').read().split('for c in sys.argv')[0])
SRC = 'dl_wbd/director_back.png'
m = cloth(SRC)
top, arm, hem = 81, 362, 950
F_TOP, F_ARM, F_HEM = 5.0, 189.0 + 0.25 * 2310.0, 1901.0
w = np.median([np.ptp(np.nonzero(m[r])[0]) for r in range(arm, arm + 8)])
cxa = np.median([(lambda z: (z.min() + z.max()) / 2)(np.nonzero(m[r])[0]) for r in range(arm, arm + 8)])
s = 905.0 / w
im = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
fy = np.arange(2000, dtype=float)
ry = np.interp(fy, [F_TOP, F_ARM, F_HEM], [top, arm, hem], left=-1e9, right=1e9)   # frame row -> photo row
rx = (np.arange(2000) - 1000.0) / s + cxa
from scipy.ndimage import map_coordinates
Y, X = np.meshgrid(ry, rx, indexing='ij')
out = np.stack([map_coordinates(im[..., k], [Y, X], order=3, cval=255.0) for k in range(3)], -1)
BL, RD, WT = np.array((0, 53, 156)), np.array((235, 7, 32)), np.array((235, 235, 246))
def snap(a, border=True):
    # this photo's colours are lighter and warmer than the AFL Store front's; each cloth pixel takes the front's colour
    # for its kind: red (r>170, g and b <130), white (all >200 and within 30 of each other: the hoop, the letters),
    # else blue (crease highlights such as 120,169,210 stay blue). Background (all >252) stays white.
    a = a.copy(); mn, mx = a.min(-1), a.max(-1)
    from scipy.ndimage import label
    bg = mn > 252   # background: near-white joined to the image border (bright pixels inside the letters are cloth)
    if border:
        lab, _ = label(bg); bg &= np.isin(lab, np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) & (lab > 0)
    else:
        bg[:] = False
    red = (a[..., 0] > 170) & (a[..., 1] < 130) & (a[..., 2] < 130); wh = (mn > 200) & (mx - mn < 30) & ~bg
    from scipy.ndimage import binary_dilation
    # pale anti-aliased outline pixels belong to the background: the upscale (2.1x across, 2.7x down) spreads the
    # photo's soft edge over ~6 px, so 8 px; not on the rows where the white hoop itself meets the side seam
    edge = binary_dilation(bg, iterations=8) & (mn > 200)
    edge[((mn > 200) & (mx - mn < 30) & ~bg).sum(1) > 300] = False
    a[~bg] = BL; a[red & ~bg] = RD; a[wh] = WT; a[bg | edge] = 255
    return a
Image.fromarray(np.clip(np.rint(out), 0, 255).astype(np.uint8)).save('ref/WBD_back_placed.png')   # the board's photo panel
out = snap(out)
# white patches left on the outline (the soft edge at the stretched shoulders) are not cloth details: any white patch
# under 2000 px (the hoop is ~120,000) goes to background if it touches it, else blue; the letters are pasted after.
from scipy.ndimage import label, binary_dilation
isw = (out == WT).all(-1); isb = (out == 255).all(-1); lab, n = label(isw)
sz = np.bincount(lab.ravel()); small = (sz < 2000); small[0] = False
for i in np.nonzero(small)[0]:
    blob = lab == i
    out[blob] = 255 if (binary_dilation(blob, iterations=2) & isb).any() else BL
print('outline white patches cleared:', int(small.sum()))
# F.F.C.: the top-armpit stretch (2.71 a px down, 2.11 across) would make the letters 1.28x too tall, so their area
# (raw x 472-542, rows 113-137) goes blue and the letters are pasted at the chest scale both ways, on the same centre.
x0, y0, x1, y1 = 466, 109, 548, 141
fx0, fx1 = (x0 - cxa) * s + 1000, (x1 - cxa) * s + 1000
fy0, fy1 = np.interp([y0, y1], [top, arm, hem], [F_TOP, F_ARM, F_HEM])
out[int(fy0):int(np.ceil(fy1)) + 1, int(fx0):int(np.ceil(fx1)) + 1] = BL
L = Image.open(SRC).convert('RGB').crop((x0, y0, x1, y1))
L = np.asarray(L.resize((round((x1 - x0) * s), round((y1 - y0) * s)), Image.LANCZOS)).astype(float)
L = snap(L, border=False); h, wd = L.shape[:2]
cy, cx0 = (fy0 + fy1) / 2, (fx0 + fx1) / 2
py, px = round(cy - h / 2), round(cx0 - wd / 2)
out[py:py + h, px:px + wd] = L
print('F.F.C. pasted at rows %d-%d, x %d-%d' % (py, py + h, px, px + wd))
Image.fromarray(np.clip(np.rint(out), 0, 255).astype(np.uint8)).save('ref/WBD_back_photo.png')
print('back placed: chest %.0f px -> 905 (x %.3f); top-armpit x %.3f, armpit-hem x %.3f' %
      (w, s, (F_ARM - F_TOP) / (arm - top), (F_HEM - F_ARM) / (hem - top if False else hem - arm)))
