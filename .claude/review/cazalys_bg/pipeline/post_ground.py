"""Hand-made ground pass on prep/ground_baked.png (no photo pixels):
grass: two-scale repeat break (45 m, 160 m) everywhere, mowing stripes (8 m) on open grass near the ground;
water: darker channel down the middle, muddy-olive banks 0-3 m, slow ripple tone. usage: post_ground.py name"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS = None
H = os.path.dirname(os.path.abspath(__file__)); name = sys.argv[1]
D = os.path.join(H, 'data', name, 'prep'); NE = json.load(open(os.path.join(D, 'meta.json')))['near']
spec = json.load(open(os.path.join(H, 'spec', name + '.json'))); P = spec['palette']
B = np.asarray(Image.open(os.path.join(D, 'ground_baked.png')).convert('RGB')).astype(np.float32); S = B.shape[0]; mpp = 2 * NE / S
G = np.asarray(Image.open(os.path.join(D, 'ground.png')).convert('RGB').resize((S, S), Image.NEAREST)).astype(np.int16)
_PC = [k for k in ('ground_default', 'spinifex', 'lawn', 'yard', 'rock', 'sand', 'water', 'road', 'path', 'ballast', 'paved', 'parking', 'track') if k in P]
_LAB = np.argmin(np.stack([np.abs(G - np.array(P[k])).sum(2) for k in _PC]), 0)   # nearest class: anti-aliased edge pixels join a side
def near(c, t):
    for i, k in enumerate(_PC):
        if P[k] == list(c): return _LAB == i
    return (np.abs(G - np.array(c)).sum(2) < t)
grass = near(P['ground_default'], 14) | near(P['lawn'], 14) | near(P['yard'], 14) | near(P['spinifex'], 14)
water = near(P['water'], 14)
rng = np.random.default_rng(3)
def lowf(cell_m):
    k = max(2, int(S * mpp / cell_m)); n = rng.random((k, k))
    return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32) / 255 - 0.5
rb = 1 + 0.035 * lowf(45) + 0.025 * lowf(160)   # patch noise within +-3% (texture session v7)
yy, xx = (np.mgrid[0:S, 0:S] + 0.5) * mpp - NE; yy = -yy           # rows run north -> south
r = np.hypot(xx, yy)
dg = ndi.distance_transform_edt(grass) * mpp                        # metres to the nearest non-grass
stripe = np.where((yy // 6) % 2 == 0, 1.03, 0.97)   # one straight set, 6 m, +-3%, parallel to the ground's long (E-W) axis (texture session v10 item 2)
mow = (dg > 4) & (r < spec.get('mow_r_m', 450))
F = np.ones((S, S), np.float32); F[grass] = rb[grass]; F[mow] *= stripe[mow]
B *= F[..., None]
# smooth the 1.5 m staircase out of the class masks: blur at full res, threshold at 0.5 (texture session v10 item 4)
def smooth(m, r_m=2.5): return ndi.gaussian_filter(m.astype(np.float32), r_m / mpp) > 0.5
w0 = water; water = smooth(water)
lost = ndi.binary_dilation(w0, iterations=10) & ~water           # staircase teeth now outside the channel: refill from the land around them
keep = ~ndi.binary_dilation(w0, iterations=10); km = ndi.gaussian_filter(keep.astype(np.float32), 2 / mpp)
for ch in range(3):
    fill = ndi.gaussian_filter(np.where(keep, B[..., ch], 0).astype(np.float32), 2 / mpp) / np.maximum(km, 1e-4)
    B[..., ch][lost] = fill[lost]
del km, keep, w0
dw = ndi.distance_transform_edt(water) * mpp
bank = water & (dw < 3); chan = np.clip((dw - 3) / 10, 0, 1)
rip = 1 + 0.07 * lowf(30) + 0.05 * lowf(90)
wc = np.array([52, 84, 90], np.float32)    # hand-picked creek tone; repaints the whole smoothed channel so no baked blue leaks past it (item 3)
B[water] = wc * ((1 - 0.32 * chan[water]) * rip[water])[:, None]
bc = np.array([96, 104, 70], np.float32); t = ((1 - dw[bank] / 3) * 0.7).astype(np.float32)[:, None]
B[bank] = B[bank] * (1 - t) + bc * t   # in place, float32 (8192^2 float64 ran out of memory)
# paved/parking: drop the 4 m grass-detail tile (read as clouds), keep a 0.5 m grain within +-3% (texture session v7 item 3)
pav = smooth(near(P['paved'], 14) | near(P['parking'], 14)) & ~water
pm = ndi.gaussian_filter(pav.astype(np.float32), 6 / mpp)
gr = 1 + 0.06 * lowf(0.5)
for ch in range(3):
    sm = ndi.gaussian_filter(np.where(pav, B[..., ch], 0).astype(np.float32), 6 / mpp) / np.maximum(pm, 1e-4)
    B[..., ch][pav] = sm[pav] * gr[pav]
del pm, gr
# grass within 4 m of paving carries the bake's grey blend: refill it from grass further out so the edge is hard (item 4)
dp = ndi.distance_transform_edt(~pav) * mpp; smear = ~pav & ~water & (dp < 4) & ndi.binary_dilation(grass, iterations=12);
gk = grass & (dp >= 4)
gm = ndi.gaussian_filter(gk.astype(np.float32), 3 / mpp)
for ch in range(3):
    fill = ndi.gaussian_filter(np.where(gk, B[..., ch], 0).astype(np.float32), 3 / mpp) / np.maximum(gm, 1e-4)
    B[..., ch][smear] = fill[smear]
del gm, dp
# hard concrete kerb, 0.3 m, where paving meets grass (item 4)
kerb = ndi.binary_dilation(pav, iterations=1) & ~pav & ndi.binary_dilation(grass, iterations=8)   # one pixel just outside the forecourt mesh edge
B[kerb] = np.array([168, 166, 158], np.float32)
Image.fromarray(np.clip(B, 0, 255).astype(np.uint8)).save(os.path.join(D, 'ground_baked.png'))
print('post_ground grass %.1f%% mow %.1f%% water %.2f%%' % (grass.mean() * 100, mow.mean() * 100, water.mean() * 100))
