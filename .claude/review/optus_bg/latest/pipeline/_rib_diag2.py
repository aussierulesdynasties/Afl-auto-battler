# band trace diagnostic: aerial | traced band outlines on aerial | muted hand-made recolour
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R = 0.5; N = 1500
x0, x1, y0, y1 = 90, 242, -128, 126
SG = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
s = Image.open('data/optus/sat.png').convert('RGB').crop((int((x0 + N) / R), int((N - y1) / R), int((x1 + N) / R), int((N - y0) / R)))
a = np.asarray(s).astype(np.float32) / 255
ref = np.array([[0.70, 0.50, 0.46], [0.80, 0.73, 0.64], [0.58, 0.55, 0.53]], np.float32)
t = ((a[..., None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1); ok = a.mean(2) >= 0.32
F = np.stack([ndi.gaussian_filter(((t == k) & ok).astype(np.float32), SG / R) for k in range(3)], -1)
lab = F.argmax(-1)
# drop islands smaller than 6 m2 (speckle), merging them into the surrounding band
for k in range(3):
    l, n = ndi.label(lab == k); sz = ndi.sum(np.ones_like(l), l, range(1, n + 1))
    small = np.isin(l, 1 + np.nonzero(sz * R * R < 6)[0])
    if small.any():
        F2 = F.copy(); F2[..., k] = -1; lab[small] = F2[small].argmax(-1)
np.save('_band_lab.npy', lab)
edge = ndi.grey_dilation(lab, 2) != ndi.grey_erosion(lab, 2)
o = np.asarray(s).copy(); o[edge] = (255, 0, 0)
tones = np.array([[178, 142, 126], [206, 194, 176], [160, 153, 145]], np.uint8)
rc = tones[lab]; rc[a.mean(2) < 0.32] = (40, 70, 40)
W = s.size[0]
big = Image.new('RGB', (W * 3 + 20, s.size[1])); big.paste(s, (0, 0)); big.paste(Image.fromarray(o), (W + 10, 0)); big.paste(Image.fromarray(rc), (2 * W + 20, 0))
big.crop((0, 0, big.size[0], 700)).resize((big.size[0] * 2 // 1, 1400), Image.NEAREST).save('_band_diag.png')
cnt = {k: int(ndi.label(lab == k)[1]) for k in range(3)}
print('bands per tone (salmon, beige, grey):', cnt)
