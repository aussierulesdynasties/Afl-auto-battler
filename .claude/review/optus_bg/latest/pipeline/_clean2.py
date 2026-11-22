# clean v2 trace: clip each field to (plaza outline minus stadium fence ellipse) instead of dropping it, drop white
# objects and pieces < 4 m2, merge duplicates (IoU > 0.8), tone each piece from its own aerial pixels
import json, numpy as np
from PIL import Image, ImageDraw
from skimage import color
from shapely.geometry import Polygon, Point
from shapely import affinity
R = 0.125; AX0, AY1 = 80, 135
raw = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')); lab = color.rgb2lab(raw / 255.0)
H = json.load(open('spec/optus_fc_hand.json.v2'))
fence = affinity.scale(Point(-16, 0).buffer(1, 128), 143, 128)
area = Polygon(H['outline']).buffer(0).difference(fence)
def px(x, y): return ((x - AX0) / R, (AY1 - y) / R)
keep, log = [], []
for i, b in enumerate(H['bands']):
    g = Polygon(b['pts']).buffer(0).intersection(area)
    for part in getattr(g, 'geoms', [g]):
        if part.geom_type != 'Polygon' or part.area < 4: continue
        if any(part.intersection(k[0]).area / part.union(k[0]).area > 0.8 for k in keep): log.append('F%02d dup' % i); continue
        mi = Image.new('L', raw.shape[1::-1], 0); ImageDraw.Draw(mi).polygon([px(*q) for q in part.exterior.coords], fill=1)
        m = np.asarray(mi) > 0
        if m.sum() < 20: continue
        L, a = np.median(lab[m][:, 0]), np.median(lab[m][:, 1])
        if L > 92: log.append('F%02d white L%.0f' % (i, L)); continue
        tone = 0 if a > 8 else (1 if L > 70 else 2)
        if tone == 0: log.append('F%02d salmon a%.1f' % (i, a)); continue
        keep.append((part, tone, i))
H['bands'] = [{'tone': t, 'pts': [[round(x, 2), round(y, 2)] for x, y in list(p.exterior.coords)[:-1]], 'holes': [[[round(x, 2), round(y, 2)] for x, y in list(h.coords)[:-1]] for h in p.interiors]} for p, t, _ in keep]
json.dump(H, open('spec/optus_fc_hand.json', 'w'), indent=1)
print(' '.join(log)); print('kept', len(keep), 'from', sorted(set(k[2] for k in keep)))
