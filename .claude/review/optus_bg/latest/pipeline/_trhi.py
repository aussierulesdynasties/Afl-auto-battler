# trace paving tone fields from the z19 aerial (reference only; only the polygons are kept). 3 tones: salmon, light beige, grey.
import json, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import measure, color
R = 0.125; AX0, AY1 = 80, 135; SIG, MINA, TOL = map(float, sys.argv[1:4])
im = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')).astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(im, (2, 2, 0)))
C = np.array([[float(v) for v in s.split(',')] for s in sys.argv[4].split(';')])   # Lab centres
veg = (im[..., 1] > im[..., 0] - 0.02) | (lab[..., 0] < 40)
D = ((lab[..., None, :] - C[None, None]) ** 2 * np.array([0.5, 1, 1])).sum(-1)
F = np.stack([ndi.gaussian_filter(((D.argmin(-1) == k) & ~veg).astype(np.float32), SIG / R) for k in range(len(C))], -1)
cls = F.argmax(-1); cls[ndi.gaussian_filter(veg.astype(np.float32), 0.5 / R) > 0.5] = -1
polys = []
for k in range(len(C)):
    m = np.pad((cls == k).astype(np.float32), 1)
    for c in measure.find_contours(ndi.gaussian_filter(m, 1.0), 0.5):
        c = measure.approximate_polygon(c - 1, TOL / R)
        if len(c) < 4: continue
        a = 0.5 * abs(np.dot(c[:, 0], np.roll(c[:, 1], 1)) - np.dot(c[:, 1], np.roll(c[:, 0], 1))) * R * R
        if a < MINA: continue
        polys.append({'tone': k, 'area': round(a), 'pts': np.column_stack([AX0 + c[:, 1] * R, AY1 - c[:, 0] * R]).round(2).tolist()})
polys.sort(key=lambda p: -p['area']); json.dump({'bands': polys}, open('_trhi.json', 'w'))
print('per tone', [sum(p['tone'] == k for p in polys) for k in range(len(C))])
col = [(205, 150, 130), (225, 205, 180), (165, 160, 155)]
fl = Image.new('RGB', (im.shape[1], im.shape[0]), (60, 90, 50)); d = ImageDraw.Draw(fl)
for p in polys: d.polygon([((x - AX0) / R, (AY1 - y) / R) for x, y in p['pts']], fill=col[p['tone']], outline=(40, 30, 30))
a = Image.open('data/optus/sat_hi_plaza.png'); s = Image.new('RGB', (a.size[0] * 2, a.size[1])); s.paste(a, (0, 0)); s.paste(fl, (a.size[0], 0)); s.resize((s.size[0] // 2, s.size[1] // 2)).save('_trhi.jpg', quality=85)
