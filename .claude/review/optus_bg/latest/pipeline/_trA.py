# Trace the Optus plaza tone fields from the z19 aerial (reference only; only vector polygons leave this script).
# Rules (Lab of the aerial smoothed 0.5 m): salmon = a* > A_T; pale beige = a* <= A_T and L > L_T; grey-taupe = the rest.
# Each class map is smoothed SIG m (generalisation), vectorised, simplified to TOL m, corners rounded (Chaikin x2).
import json, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import color, measure
R = 0.125; AX0, AY1 = 80, 135
A_T, L_T, SIG, MINA, TOL = map(float, sys.argv[1:6])
im = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')).astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(im, (4, 4, 0)))
veg = (im[..., 1] > im[..., 0] - 0.01) | (lab[..., 0] < 45)
c = np.where(lab[..., 1] > A_T, 0, np.where(lab[..., 0] > L_T, 1, 2))
F = np.stack([ndi.gaussian_filter(((c == k) & ~veg).astype(np.float32), SIG / R) for k in range(3)], -1)
cls = F.argmax(-1)
out = []
for k in (1, 2):
    m = np.pad((cls == k).astype(np.float32), 1)
    for ct in measure.find_contours(m, 0.5):
        ct = measure.approximate_polygon(ct - 1, TOL / R)
        if len(ct) < 4: continue
        for _ in range(2):
            q = np.roll(ct, -1, 0); ct = np.stack([0.75 * ct + 0.25 * q, 0.25 * ct + 0.75 * q], 1).reshape(-1, 2)
        a = 0.5 * abs(np.dot(ct[:, 0], np.roll(ct[:, 1], 1)) - np.dot(ct[:, 1], np.roll(ct[:, 0], 1))) * R * R
        if a < MINA: continue
        out.append({'tone': k, 'area': round(a), 'pts': np.column_stack([AX0 + ct[:, 1] * R, AY1 - ct[:, 0] * R]).round(2).tolist()})
out.sort(key=lambda p: -p['area'])
json.dump({'bands': out}, open('_trA.json', 'w'))
print('pale', sum(p['tone'] == 1 for p in out), 'grey', sum(p['tone'] == 2 for p in out))
a = Image.open('data/optus/sat_hi_plaza.png').convert('RGB'); ov = a.copy(); d = ImageDraw.Draw(ov)
fl = Image.new('RGB', a.size, (205, 150, 130)); d2 = ImageDraw.Draw(fl)
for p in sorted(out, key=lambda p: -p['area']):
    pts = [((x - AX0) / R, (AY1 - y) / R) for x, y in p['pts']]
    d.line(pts + [pts[0]], fill=(0, 255, 255) if p['tone'] == 1 else (255, 0, 255), width=3)
    d2.polygon(pts, fill=(232, 215, 190) if p['tone'] == 1 else (160, 152, 146))
s = Image.new('RGB', (a.size[0] * 2, a.size[1])); s.paste(ov, (0, 0)); s.paste(fl, (a.size[0], 0)); s.resize((s.size[0] // 2, s.size[1] // 2)).save('_trA.jpg', quality=85)
