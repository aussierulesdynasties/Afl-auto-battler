# Facet trace: the Optus plaza bands are straight-edged facets of 4 paver tones. Segment the aerial (reference only)
# into tones, keep regions >= MINA m2, vectorise each region's outline and simplify to straight edges (tolerance TOL m).
import json, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure, color
NEAR = 1500; SR = 0.5
X0, X1, Y0, Y1 = 95, 245, -15, 126
SIG, MINA, TOL = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
sat = Image.open('data/optus/sat.png').convert('RGB')
box = (int((X0 + NEAR) / SR), int((NEAR - Y1) / SR), int((X1 + NEAR) / SR), int((NEAR - Y0) / SR))
cr = np.asarray(sat.crop(box)).astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(cr, (0.7, 0.7, 0)))
green = (cr[..., 1] > cr[..., 0] + 0.01) & (cr[..., 1] > cr[..., 2])
pave = (lab[..., 0] > 52) & ~green & (np.hypot(lab[..., 1], lab[..., 2]) < 32)
pave = ndi.binary_opening(pave, iterations=2)
# tone centres (Lab) read from the aerial: salmon base, dark red, beige, grey
C = np.array([[66, 14, 14], [58, 19, 15], [76, 5, 15], [66, 3, 6]], np.float32)
D = ((lab[..., None, :] - C[None, None]) ** 2 * np.array([0.6, 1, 1])).sum(-1)
F = np.stack([ndi.gaussian_filter(((D.argmin(-1) == k) & pave).astype(np.float32), SIG / SR) for k in range(4)], -1)
cls = np.where(ndi.gaussian_filter(pave.astype(np.float32), SIG / SR) > 0.5, F.argmax(-1), -1)
for it in range(3):   # merge small islands into the neighbouring tone
    for k in range(4):
        l, n = ndi.label(cls == k)
        if n == 0: continue
        sz = ndi.sum(np.ones_like(l), l, range(1, n + 1)) * SR * SR
        for i in np.nonzero(sz < MINA)[0]:
            m = l == i + 1; ring = ndi.binary_dilation(m, iterations=2) & ~m
            v = cls[ring]; v = v[v >= 0]
            cls[m] = np.bincount(v, minlength=4).argmax() if len(v) else -1
polys = []
for k in range(4):
    m = np.pad((cls == k).astype(np.float32), 1)
    for c in measure.find_contours(ndi.gaussian_filter(m, 0.7), 0.5):
        c = measure.approximate_polygon(c - 1, TOL / SR)
        if len(c) < 4: continue
        a = 0.5 * abs(np.dot(c[:, 0], np.roll(c[:, 1], 1)) - np.dot(c[:, 1], np.roll(c[:, 0], 1))) * SR * SR
        if a < MINA: continue
        polys.append({'tone': k, 'area': round(a, 1), 'pts': np.column_stack([X0 + c[:, 1] * SR, Y1 - c[:, 0] * SR]).round(2).tolist()})
polys.sort(key=lambda p: -p['area'])
json.dump({'bands': polys}, open('data/optus/prep/fc_polys.json', 'w'))
print('regions per tone', [sum(p['tone'] == k for p in polys) for k in range(4)])
S = 3; W, H = cr.shape[1] * S, cr.shape[0] * S
ov = sat.crop(box).resize((W, H)); fl = Image.new('RGB', (W, H), (90, 110, 70)); d2 = ImageDraw.Draw(fl); d1 = ImageDraw.Draw(ov)
col = [(200, 140, 125), (165, 95, 85), (225, 210, 185), (175, 165, 160)]
for p in polys:   # big first, holes come out as later smaller polygons of the other tone
    pts = [((x - X0) / SR * S, (Y1 - y) / SR * S) for x, y in p['pts']]
    d2.polygon(pts, fill=col[p['tone']], outline=(60, 40, 40)); d1.line(pts + [pts[0]], fill=(0, 255, 255), width=1)
im = Image.new('RGB', (2 * W, H)); im.paste(ov, (0, 0)); im.paste(fl, (W, 0)); im.save('_trace2.jpg', quality=88)
