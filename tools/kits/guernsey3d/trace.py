# Trace a guernsey photo into a flat design: every cloth pixel snapped to the club's colours,
# sponsors and logos filled with the colour round them, the neck lining and background cut out.
# python trace.py CODE side "#hex,#hex" "x0,y0,x1,y1;..." out.png
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
code, side, pal, boxes, out = sys.argv[1:6]
hole_pts = sys.argv[6] if len(sys.argv) > 6 else ''
a = np.array(Image.open(f'ref/{code}_{side}.png').convert('RGB')).astype(float)
P = np.array([[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in pal.split(',')], float)
light = a.min(-1) > 200
lab, _ = nd.label(light)
edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
bg = np.isin(lab, list(edge))
# light areas enclosed by cloth: a logo if it lies inside a box, else the neck's lining seen through the neck
logo = np.zeros(light.shape, bool)
for b in [x for x in boxes.split(';') if x]:
    x0, y0, x1, y1 = map(int, b.split(','))
    x0, y0, x1, y1 = x0 - 20, y0 - 20, x1 + 20, y1 + 20
    logo[y0:y1, x0:x1] = True
hole = light & ~bg & ~logo
lab2, n2 = nd.label(hole)
sizes = nd.sum(np.ones_like(lab2), lab2, range(1, n2 + 1))
lining = np.isin(lab2, [i + 1 for i, s in enumerate(sizes) if s > 1500])
if lining.any():
    # the neck opening is one convex shape: the lining and the tags printed on it
    from scipy.spatial import ConvexHull
    from matplotlib.path import Path
    yy, xx = np.nonzero(lining)
    h = ConvexHull(np.c_[xx, yy])
    poly = Path(np.c_[xx, yy][h.vertices])
    y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    gy, gx = np.mgrid[y0:y1, x0:x1]
    lining[y0:y1, x0:x1] |= poly.contains_points(np.c_[gx.ravel(), gy.ravel()], radius=6).reshape(gy.shape)
if hole_pts:
    # the neck opening traced off the photo's grid (the inner edge of the front binding)
    from matplotlib.path import Path
    pts = np.array([[float(v) for v in p.split(',')] for p in hole_pts.split(';')])
    gy, gx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lining = Path(pts).contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gy.shape)
cloth = ~bg & ~lining
cloth = nd.binary_opening(nd.binary_closing(cloth, iterations=2), iterations=2)
d = ((a[..., None, :] - P[None, None]) ** 2).sum(-1)
k = d.argmin(-1)
known = cloth & ~logo & (np.sqrt(d.min(-1)) < 70)
_, (iy, ix) = nd.distance_transform_edt(~known, return_indices=True)
k = k[iy, ix]
# Vector redraw: every colour region's edge is traced as a curve, the stretches inside a sponsor
# box are bridged by a cubic carried on from the edge either side, every edge is smoothed (no pixel
# steps), and the regions are drawn again at 4x and scaled down (clean edges, no photo speckle).
import cv2
boxl = []
for bx in [x for x in boxes.split(';') if x]:
    x0, y0, x1, y1 = map(int, bx.split(','))
    boxl.append((x0 - 20, y0 - 20, x1 + 20, y1 + 20))
def in_box(p):
    return any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for x0, y0, x1, y1 in boxl)
def smooth_curve(c):
    c = c.astype(float)
    m = np.array([in_box(p) for p in c])
    n = len(c)
    if m.any() and not m.all():
        # walk from a point outside the boxes, bridge each run of box points
        start = int(np.argmin(m))
        c = np.roll(c, -start, 0); m = np.roll(m, -start)
        i = 0
        while i < n:
            if not m[i]:
                i += 1; continue
            j = i
            while j < n and m[j]:
                j += 1
            K = 60
            pre = c[max(0, i - K):i]; post = c[j:min(n, j + K)]
            if len(pre) > 5 and len(post) > 5:
                t = np.r_[np.arange(-len(pre), 0), np.arange(j - i, j - i + len(post))].astype(float)
                pts = np.r_[pre, post]
                tt = np.arange(0, j - i).astype(float)
                for d in range(2):
                    co = np.polyfit(t, pts[:, d], 3)
                    c[i:j, d] = np.polyval(co, tt)
            i = j
    # smooth (closed curve)
    k1 = np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2); k1 /= k1.sum()
    ext = np.r_[c[-9:], c, c[:9]]
    return np.stack([np.convolve(ext[:, d], k1, 'valid') for d in range(2)], -1)
U = 4
Hh, Ww = k.shape
def raster(mask):
    cs, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = np.zeros((Hh * U, Ww * U), np.uint8)
    if hier is None:
        return out
    for ci, cc in enumerate(cs):
        if len(cc) < 20:
            continue
        cv = np.round(smooth_curve(cc[:, 0, :]) * U).astype(np.int32)
        hole = hier[0][ci][3] >= 0
        cv2.fillPoly(out, [cv], 0 if hole else 1)
    return out
shape = raster(cloth).astype(np.float32)
layers = [shape * 0 + 1] + [raster(cloth & (k == c)).astype(np.float32) for c in range(1, len(P))]
kk = np.zeros((Hh * U, Ww * U), np.uint8)
for c in range(1, len(P)):
    kk[layers[c] > 0] = c
col = P[kk].astype(np.float32)
img4 = np.dstack([col, shape[..., None] * 255])
img = cv2.resize(img4, (Ww, Hh), interpolation=cv2.INTER_AREA)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)
print(out, 'cloth px', cloth.sum(), 'colours', len(P))
raise SystemExit
img = np.zeros(a.shape[:2] + (4,), np.uint8)
img[..., :3] = P[k].astype(np.uint8)
img[..., 3] = cloth * 255
Image.fromarray(img).save(out)
print(out, 'cloth px', cloth.sum(), 'logo px filled', (logo & cloth).sum(), 'lining px', lining.sum(), 'counts', np.bincount(k[cloth], minlength=len(P)))
