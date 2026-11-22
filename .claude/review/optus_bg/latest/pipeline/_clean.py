# clean the traced fields: drop fields outside the plaza outline or on white non-paving objects, merge duplicate
# polygons (same outline traced as both tones), and give each kept field the tone its aerial pixels are closest to
import json, numpy as np
from PIL import Image, ImageDraw
from skimage import color
from matplotlib.path import Path
R = 0.125; AX0, AY1 = 80, 135
raw = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB'))
lab = color.rgb2lab(raw / 255.0)
H = json.load(open('spec/optus_fc_hand.json')); O = Path(H['outline'])
def px(x, y): return ((x - AX0) / R, (AY1 - y) / R)
seen = {}; keep = []; log = []
for i, b in enumerate(H['bands']):
    p = np.array(b['pts']); key = tuple(np.round(p.mean(0), 1)) + (round(len(p) / 2),)
    mi = Image.new('L', raw.shape[1::-1], 0); ImageDraw.Draw(mi).polygon([px(*q) for q in p], fill=1); m = np.asarray(mi) > 0
    xs, ys = np.meshgrid(AX0 + (np.arange(raw.shape[1]) + .5) * R, AY1 - (np.arange(raw.shape[0]) + .5) * R)
    pts = np.c_[xs[m], ys[m]]; fin = O.contains_points(pts).mean() if len(pts) else 0
    fence = (((pts[:, 0] + 16) / 143) ** 2 + (pts[:, 1] / 128) ** 2 < 1).mean() if len(pts) else 1
    L = np.median(lab[m][:, 0]) if m.any() else 100; a = np.median(lab[m][:, 1]) if m.any() else 0
    if fin < 0.5: log.append('F%02d drop: %.0f%% outside plaza outline' % (i, 100 - 100 * fin)); continue
    if fence > 0.5: log.append('F%02d drop: inside stadium fence' % i); continue
    if L > 92: log.append('F%02d drop: white object (L %.0f), not paving' % (i, L)); continue
    tone = 0 if a > 8 else (1 if L > 70 else 2)
    if key in seen: log.append('F%02d drop: duplicate of F%02d' % (i, seen[key])); continue
    seen[key] = i
    if tone == 0: log.append('F%02d drop: aerial reads salmon base (a* %.1f)' % (i, a)); continue
    if tone != b['tone']: log.append('F%02d retone %d -> %d (L %.0f a* %.1f)' % (i, b['tone'], tone, L, a))
    keep.append({'tone': tone, 'pts': b['pts']})
H['bands'] = keep; json.dump(H, open('spec/optus_fc_hand.json', 'w'), indent=1)
print('\n'.join(log)); print('kept', len(keep))
