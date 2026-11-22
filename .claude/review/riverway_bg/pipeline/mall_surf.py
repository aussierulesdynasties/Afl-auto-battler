"""Measured from the aerial (reference only): 1 m cells of ground car park (grey asphalt) and of rooftop parking deck
(tan concrete on a big building) inside spec 'carport_box'. python -E mall_surf.py spec.json"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
Image.MAX_IMAGE_PIXELS = None
sp = json.load(open(sys.argv[1])); D = 'data/%s/' % sp['name']
sj = json.load(open(D + 'sat.json')); H, MP = sj['half_m'], sj['m_per_px']
s = np.asarray(Image.open(D + 'sat.png').convert('RGB')).astype(np.float32)
bx0, by0, bx1, by1 = sp['carport_box']
X0, Y0 = int((bx0 + H) / MP), int((H - by1) / MP); X1, Y1 = int((bx1 + H) / MP), int((H - by0) / MP)
a = s[Y0:Y1, X0:X1]; r, g, b = a[..., 0], a[..., 1], a[..., 2]; v = (r + g + b) / 3; sat = a.max(2) - a.min(2)
BL = json.load(open(D + 'prep/buildings.json'))
fp = Image.new('L', (X1 - X0, Y1 - Y0), 0); df = ImageDraw.Draw(fp)
big = Image.new('F', (X1 - X0, Y1 - Y0), 0.0); dbg = ImageDraw.Draw(big)
for bl in BL:
    q = [((x + H) / MP - X0, (H - y) / MP - Y0) for x, y in bl['p']]
    df.polygon(q, fill=1)
    P = np.array(bl['p']); A = 0.5 * abs(np.dot(P[:, 0], np.roll(P[:, 1], 1)) - np.dot(P[:, 1], np.roll(P[:, 0], 1)))
    if bl['c'] != 'house' and A > 20000: dbg.polygon(q, fill=float(bl['h']))
fp = np.asarray(fp) > 0; big = np.asarray(big)
cp = json.load(open(D + 'prep/carports.json'))
green = (g > r * 1.02) & (g > b * 1.02)
def zmask(polys):
    z = Image.new('L', (X1 - X0, Y1 - Y0), 0); dz = ImageDraw.Draw(z)
    for P in polys: dz.polygon([((x + H) / MP - X0, (H - y) / MP - Y0) for x, y in P], fill=1)
    return np.asarray(z) > 0
asph = (sat < 34) & (v > 55) & (v < 180) & ~green & ~fp & zmask(sp['park_zones'])
asph = nd.binary_opening(nd.binary_closing(asph, iterations=3), iterations=2)
lab, n = nd.label(asph); sz = nd.sum(asph, lab, range(1, n + 1)) * MP * MP
asph = np.isin(lab, 1 + np.nonzero(sz >= 300)[0])
_fh = nd.binary_fill_holes(asph) & ~asph; lab2, n2 = nd.label(_fh); sz2 = nd.sum(_fh, lab2, range(1, n2 + 1)) * MP * MP
asph |= np.isin(lab2, 1 + np.nonzero(sz2 < 300)[0]) & ~fp   # car specks and small paint marks inside a lot
deck = (big > 0) & zmask([sp['deck_zone']]) & (v < 212) & (r > b + 12) & (sat < 60)
deck = nd.binary_opening(nd.binary_closing(deck, iterations=3), iterations=3)
lab, n = nd.label(deck); sz = nd.sum(deck, lab, range(1, n + 1)) * MP * MP
deck = np.isin(lab, 1 + np.nonzero(sz >= 400)[0])
roof = (big > 0) & ~deck
print('big roof (non-deck) median', np.median(a[nd.binary_erosion(roof, iterations=4)], 0).astype(int).tolist(),
      'deck median', np.median(a[deck], 0).astype(int).tolist(), 'asphalt median', np.median(a[asph], 0).astype(int).tolist())
k = int(round(1 / MP)); hh, ww = asph.shape[0] // k, asph.shape[1] // k
def cells(m, extra=None):
    mc = m[:hh * k, :ww * k].reshape(hh, k, ww, k).mean((1, 3)) >= 0.5; jj, ii = np.nonzero(mc)
    out = [[round(bx0 + (i + 0.5) * k * MP, 1), round(by1 - (j + 0.5) * k * MP, 1)] for j, i in zip(jj, ii)]
    if extra is not None:
        e = extra[:hh * k, :ww * k].reshape(hh, k, ww, k).max((1, 3)); out = [o + [float(e[j, i])] for o, j, i in zip(out, jj, ii)]
    return out
P_, D_ = cells(asph), cells(deck, big)
json.dump(P_, open(D + 'prep/park_cells.json', 'w')); json.dump(D_, open(D + 'prep/deck_cells.json', 'w'))
print('asphalt m2', len(P_), 'deck m2', len(D_))
vis = np.zeros(asph.shape + (3,), np.uint8); vis[asph] = (90, 90, 90); vis[deck] = (220, 180, 120)
Image.fromarray(np.concatenate([vis, a.astype(np.uint8)], 1)).resize((asph.shape[1], asph.shape[0] // 2)).save('out/riverway/chk/mall_surf_mask.png')
