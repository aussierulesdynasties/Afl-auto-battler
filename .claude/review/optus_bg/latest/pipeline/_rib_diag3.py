# k-means the forecourt paving tones in the aerial; draw the overlay mask outline + band edges on the aerial
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
R = 0.5; N = 1500
x0, x1, y0, y1 = 90, 242, -128, 126
s = Image.open('data/optus/sat.png').convert('RGB').crop((int((x0 + N) / R), int((N - y1) / R), int((x1 + N) / R), int((N - y0) / R)))
a = np.asarray(s).astype(np.float32) / 255
fc = np.asarray(Image.open('data/optus/prep/forecourt.png'))
al = fc[..., 3][:, int((90 + 154) / 0.1):int((242 + 154) / 0.1)]
al = np.asarray(Image.fromarray(al).resize((a.shape[1], a.shape[0]), Image.BILINEAR)) > 128
pav = al & (a.mean(2) >= 0.32) & ~((a[..., 1] > a[..., 0]) & (a[..., 1] > a[..., 2]))
px = a[pav]
np.random.seed(1)
c, l = kmeans2(px, 3, minit='++', seed=1)
o = np.argsort(-(c[:, 0] - c[:, 2]))   # most salmon first
print('kmeans tones (0-1):', np.round(c[o], 3).tolist(), 'shares', [round(float((l == i).mean()), 2) for i in o])
out = np.asarray(s).copy()
ed = al ^ ndi.binary_erosion(al, iterations=2); out[ed] = (0, 255, 255)
Image.fromarray(out).resize((s.size[0] * 2, s.size[1] * 2)).save('_mask_on_sat.png')
