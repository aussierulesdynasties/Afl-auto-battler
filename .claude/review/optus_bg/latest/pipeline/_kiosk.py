# re-trace the two kiosk slabs: pixels near each old trace that are neutral and light (concrete), largest blob,
# boundary = rotated minimum-area rectangle with 0.6 m corner rounding (the slabs are rounded rectangles on z19)
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import color
from shapely.geometry import Polygon, MultiPoint
R = 0.125; AX0, AY1 = 80, 135
raw = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')); lab = color.rgb2lab(ndi.gaussian_filter(raw / 255.0, (1.5, 1.5, 0)))
conc = (np.abs(lab[..., 1]) < 4) & (lab[..., 2] < 12) & (lab[..., 0] > 55)
conc |= (lab[..., 0] < 30)  # dark rooftop unit sits on the slab
H = json.load(open('spec/optus_fc_hand.json')); V = json.load(open('spec/optus_fc_hand.json.v3'))
def px(x, y): return ((x - AX0) / R, (AY1 - y) / R)
for bi in (12, 13):
    b = H['bands'][bi]; g = Polygon(V['bands'][{12: 9, 13: 10}[bi]]['pts']).buffer(3)
    mi = Image.new('L', raw.shape[1::-1], 0); ImageDraw.Draw(mi).polygon([px(*q) for q in g.exterior.coords], fill=1)
    m = ndi.binary_opening(conc & (np.asarray(mi) > 0), iterations=2); m = ndi.binary_fill_holes(m)
    lb, n = ndi.label(m); k = np.argmax(ndi.sum(m, lb, range(1, n + 1))) + 1; r, c = np.nonzero(lb == k)
    pts = np.c_[AX0 + (c + .5) * R, AY1 - (r + .5) * R]
    from skimage import measure
    cs = measure.find_contours(np.pad(lb == k, 1).astype(float), 0.5); cc = max(cs, key=len) - 1
    rect = Polygon(np.c_[AX0 + (cc[:, 1] + .5) * R, AY1 - (cc[:, 0] + .5) * R]).buffer(0).convex_hull.simplify(0.15)
    # slab-edge error: model edge vs the concrete blob edge
    em = lb == k; ed = ndi.binary_dilation(em) ^ em; dd = ndi.distance_transform_edt(~ed) * R
    ev = [dd[int((AY1 - y) / R), int((x - AX0) / R)] for x, y in np.array(rect.exterior.interpolate(np.linspace(0, rect.exterior.length, 400)).coords if False else [rect.exterior.interpolate(t).coords[0] for t in np.linspace(0, rect.exterior.length, 400)])]
    print('F%d slab edge error median %.2f p90 %.2f max %.2f m' % (bi, np.median(ev), np.percentile(ev, 90), max(ev)))
    b['pts'] = [[round(x, 2), round(y, 2)] for x, y in list(rect.exterior.coords)[:-1]]; b.pop('holes', None)
    e = np.array(rect.exterior.coords); s = [np.linalg.norm(e[i + 1] - e[i]) for i in range(len(e) - 1)]
    print('F%d slab %.1f m2' % (bi, rect.area))
json.dump(H, open('spec/optus_fc_hand.json', 'w'), indent=1)
