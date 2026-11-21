# supervised tone classification of the z19 plaza aerial (reference only): LDA on Lab (smoothed 0.6 m) from hand-picked
# training patches (2.5 m squares), vegetation/shadow masked, class probabilities smoothed SIG m, argmax.
import json, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
R = 0.125; AX0, AY1 = 80, 135; SIG = float(sys.argv[1])
TR = json.load(open(sys.argv[2]))
im = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')).astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(im, (0.6 / R, 0.6 / R, 0)))
X, y = [], []
for k, (cn, pts) in enumerate(TR.items()):
    for x, yy in pts:
        j, r = int((x - AX0) / R), int((AY1 - yy) / R); X.append(lab[r - 10:r + 10, j - 10:j + 10].reshape(-1, 3)); y += [k] * 400
clf = LDA().fit(np.vstack(X), y)
veg = (im[..., 1] > im[..., 0] - 0.01) | (lab[..., 0] < 42) | (lab[..., 0] > 90)
P = clf.predict_proba(lab.reshape(-1, 3)).reshape(lab.shape[0], lab.shape[1], -1)
P = np.stack([ndi.gaussian_filter(P[..., k] * ~veg, SIG / R) for k in range(P.shape[-1])], -1)
cls = P.argmax(-1); cls[ndi.gaussian_filter((~veg).astype(np.float32), SIG / R) < 0.5] = -1
np.save('_sup.npy', cls.astype(np.int8))
pal = np.array([[215, 150, 130], [235, 220, 195], [150, 140, 135], [170, 95, 85], [40, 70, 40]], np.uint8)
a = Image.open('data/optus/sat_hi_plaza.png'); b = Image.fromarray(pal[cls]); s = Image.new('RGB', (a.size[0] * 2, a.size[1])); s.paste(a, (0, 0)); s.paste(b, (a.size[0], 0))
s.resize((s.size[0] // 2, s.size[1] // 2)).save('_sup.jpg', quality=85); print('classes', list(TR), np.bincount(cls[cls >= 0].ravel()))
