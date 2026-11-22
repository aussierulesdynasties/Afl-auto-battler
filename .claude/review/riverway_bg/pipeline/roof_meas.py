"""Set each house's roof palette index from its measured aerial roof colour (median inside the footprint, 1 m inset).
The roof keeps its hand-made texture and palette colour; only the choice of palette entry is measured.
python -E roof_meas.py spec.json"""
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
sp = json.load(open(sys.argv[1])); name = sp['name']; D = 'data/%s/' % name
sj = json.load(open(D + 'sat.json')); H, MP = sj['half_m'], sj['m_per_px']
a = np.asarray(Image.open(D + 'sat.png').convert('RGB')).astype(np.float32)
PAL = np.array(sp['palette']['roofs_house'], float)
BP = D + 'prep/buildings.json'; bk = D + 'prep/buildings_prefit.json'
if not os.path.exists(bk): json.dump(json.load(open(BP)), open(bk, 'w'))
BL = json.load(open(bk)); n = 0; hist = np.zeros(len(PAL), int)
for bl in BL:
    if bl['c'] != 'house': continue
    P = np.array(bl['p'], float); c = P.mean(0); P = c + (P - c) * 0.8   # inset off the eaves
    q = [((x + H) / MP, (H - y) / MP) for x, y in P]
    x0, y0 = np.floor(np.min(q, 0)).astype(int); x1, y1 = np.ceil(np.max(q, 0)).astype(int)
    if x0 < 0 or y0 < 0 or x1 >= a.shape[1] or y1 >= a.shape[0]: continue
    mi = Image.new('L', (x1 - x0 + 1, y1 - y0 + 1), 0); ImageDraw.Draw(mi).polygon([(u - x0, v - y0) for u, v in q], fill=1)
    k = np.asarray(mi) > 0
    if k.sum() < 8: continue
    col = np.median(a[y0:y1 + 1, x0:x1 + 1][k], 0)
    i = int(np.argmin(((PAL - col) ** 2).sum(1))); bl['roof'] = i; hist[i] += 1; n += 1
json.dump(BL, open(BP, 'w'))
print('houses measured', n, 'palette share', dict(zip(range(len(PAL)), np.round(hist / max(n, 1), 3).tolist())))

# ---- carports: footprints mostly covered by dark shade-sail pixels become sails (3.5 m canopy on posts, no walls);
# grey carport rows inside OSM parking areas (low-saturation, 120-185 grey, long thin components) are added as sails.
from scipy import ndimage as nd
import math
r, g, b = a[..., 0], a[..., 1], a[..., 2]; v = (r + g + b) / 3; sat = a.max(2) - a.min(2)
dark = (v < 105) & (b >= g * 0.95) & (b >= r * 0.95)
def fp_mask(P):
    q = [((x + H) / MP, (H - y) / MP) for x, y in P]
    x0, y0 = np.floor(np.min(q, 0)).astype(int); x1, y1 = np.ceil(np.max(q, 0)).astype(int)
    mi = Image.new('L', (x1 - x0 + 1, y1 - y0 + 1), 0); ImageDraw.Draw(mi).polygon([(u - x0, v_ - y0) for u, v_ in q], fill=1)
    return x0, y0, x1, y1, np.asarray(mi) > 0
ns = 0
for bl in BL:
    bl.pop('sail', None)
    x0, y0, x1, y1, k = fp_mask(bl['p'])
    if x0 < 0 or y0 < 0 or x1 >= a.shape[1] or y1 >= a.shape[0] or k.sum() < 40 or bl['h'] > 6: continue
    if dark[y0:y1 + 1, x0:x1 + 1][k].mean() >= 0.5: bl['sail'] = [62, 66, 78]; ns += 1
BL = [bl for bl in BL if not bl.get('sail')]   # shade-sail footprints: built as carport canopy (carports.py), not 5 m blocks
json.dump(BL, open(BP, 'w'))
print('sail footprints dropped (canopy instead)', ns)
