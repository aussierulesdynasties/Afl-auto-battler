"""data/<g>/prep/carports.json: carport/shade-sail canopy cells measured from the aerial (reference only; the canopy
gets a hand-made colour). Panel mask: bluish-grey, unsaturated, mid-dark (b >= r-6, b >= g-4, 35 < mean < 150,
sat < 50), closed 2 / opened 3 px, components >= 40 m2, inside spec 'carport_box' and outside house footprints.
Cells are 1 m; each carries the height of the roof it sits on (0 = ground; deck sails on a building get its height).
python -E carports.py spec.json"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
Image.MAX_IMAGE_PIXELS = None
sp = json.load(open(sys.argv[1])); name = sp['name']; D = 'data/%s/' % name
sj = json.load(open(D + 'sat.json')); H, MP = sj['half_m'], sj['m_per_px']
s = np.asarray(Image.open(D + 'sat.png').convert('RGB')).astype(np.float32)
bx0, by0, bx1, by1 = sp['carport_box']            # metres: x0, y0 (south), x1, y1 (north)
X0, Y0 = int((bx0 + H) / MP), int((H - by1) / MP); X1, Y1 = int((bx1 + H) / MP), int((H - by0) / MP)
a = s[Y0:Y1, X0:X1]; r, g, b = a[..., 0], a[..., 1], a[..., 2]; v = (r + g + b) / 3; sat = a.max(2) - a.min(2)
m = (b >= r - 6) & (b >= g - 4) & (v < 150) & (v > 35) & (sat < 50)
m = nd.binary_opening(nd.binary_closing(m, iterations=2), iterations=3)
BL = json.load(open(D + 'prep/buildings.json'))
hm = Image.new('L', (X1 - X0, Y1 - Y0), 0); dh = ImageDraw.Draw(hm)
lift = Image.new('F', (X1 - X0, Y1 - Y0), 0.0); dl = ImageDraw.Draw(lift)
for bl in BL:
    q = [((x + H) / MP - X0, (H - y) / MP - Y0) for x, y in bl['p']]
    if bl['c'] == 'house': dh.polygon(q, fill=1)
    elif bl['h'] > 6 and not bl.get('sail'): dl.polygon(q, fill=float(bl['h']))
m &= ~(np.asarray(hm) > 0)
lab, n = nd.label(m); sz = nd.sum(m, lab, range(1, n + 1)) * MP * MP
m = np.isin(lab, 1 + np.nonzero(sz >= 40)[0])
lift = np.asarray(lift)
k = int(round(1 / MP)); hh, ww = m.shape[0] // k, m.shape[1] // k   # 1 m cells, majority vote
mc = m[:hh * k, :ww * k].reshape(hh, k, ww, k).mean((1, 3)) >= 0.5
lc = lift[:hh * k, :ww * k].reshape(hh, k, ww, k).max((1, 3))
jj, ii = np.nonzero(mc)
C = [[round(bx0 + (i + 0.5) * k * MP, 1), round(by1 - (j + 0.5) * k * MP, 1), float(lc[j, i])] for j, i in zip(jj, ii)]
json.dump(C, open(D + 'prep/carports.json', 'w'))
print('carport cells', len(C), 'm2; on roofs', int(sum(1 for c in C if c[2] > 0)))
