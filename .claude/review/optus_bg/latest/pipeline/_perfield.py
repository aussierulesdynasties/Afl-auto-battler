# per-field table: outline error (m) and tone (aerial sRGB median vs model tone)
import json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import color
from matplotlib.path import Path
R = 0.125; AX0, AY1 = 80, 135
raw = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB'))
im = raw.astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(im, (4, 4, 0)))
c = ndi.median_filter(np.where(lab[..., 1] > 8, 0, np.where(lab[..., 0] > 70, 1, 2)), 9)
edge = ndi.grey_dilation(c, 3) != ndi.grey_erosion(c, 3)
dist = ndi.distance_transform_edt(~edge) * R
H = json.load(open('spec/optus_fc_hand.json')); sp = json.load(open('spec/optus.json'))
T = np.array(sp['forecourt_tones']); O = Path(H['outline'])
def px(x, y): return ((x - AX0) / R, (AY1 - y) / R)
def inside_ok(x, y): return O.contains_point((x, y)) and ((x + 16) / 143) ** 2 + (y / 128) ** 2 >= 1
rows = []
# aerial -> ground colour: per-channel gain from the salmon base, aerial median (201,164,142) vs sunlit ground photo E37 Open Day 018 (191,163,155)
G = np.array([191 / 201, 163 / 164, 155 / 142])
base = Image.new('L', raw.shape[1::-1], 0); ImageDraw.Draw(base).polygon([px(*p) for p in H['outline']], fill=1)
for b in H['bands']:
    ImageDraw.Draw(base).polygon([px(*p) for p in b['pts']], fill=0)
    for hh in b.get('holes', []): ImageDraw.Draw(base).polygon([px(*p) for p in hh], fill=1)
HOLES = {'F%02d' % i: b.get('holes', []) for i, b in enumerate(H['bands'])}
fields = [('base', 0, None)] + [('F%02d' % i, b['tone'], b['pts']) for i, b in enumerate(H['bands'])]
for name, tone, pts in fields:
    if pts is None: m = np.asarray(base) > 0; e = []
    else:
        mi = Image.new('L', raw.shape[1::-1], 0); ImageDraw.Draw(mi).polygon([px(*p) for p in pts], fill=1)
        for hh in HOLES.get(name, []): ImageDraw.Draw(mi).polygon([px(*p) for p in hh], fill=0)
        m = np.asarray(mi) > 0
        p = np.array(pts); e = []
        for (x0, y0), (x1, y1) in zip(p, np.roll(p, -1, 0)):
            for t in np.linspace(0, 1, 6, endpoint=False):
                x, y = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                if not inside_ok(x, y): continue
                j, r = int((x - AX0) / R), int((AY1 - y) / R)
                if 0 <= r < dist.shape[0] and 0 <= j < dist.shape[1]: e.append(dist[r, j])
    m &= ~((lab[..., 1] < -2) | (lab[..., 0] < 45))   # drop vegetation/shadow pixels from the tone sample
    if m.sum() < 50: rows.append((name, tone, None, None, None, None)); continue
    med = np.median(raw[m], 0) * G; mod = T[tone]
    dE = np.linalg.norm(color.rgb2lab(med[None, None] / 255)[0, 0] - color.rgb2lab(mod[None, None] / 255)[0, 0])
    area = m.sum() * R * R
    rows.append((name, tone, area, np.median(e) if e else None, np.percentile(e, 90) if e else None, (med, mod, dE)))
print('field tone area_m2 err_med err_p90 aerial_rgb_calibrated model_rgb dE')
for n, t, a, em, e9, tc in rows:
    if a is None: print(n, t, 'too small/occluded'); continue
    print(n, t, '%.0f' % a, '%.2f' % em if em is not None else '-', '%.2f' % e9 if e9 is not None else '-', tuple(int(v) for v in tc[0]), tuple(int(v) for v in tc[1]), '%.1f' % tc[2])
