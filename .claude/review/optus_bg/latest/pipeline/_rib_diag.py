# ribbon trace diagnostic: aerial crop with traced centre lines (red), current vs new method, side by side
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, remove_small_objects, white_tophat, disk
R = 0.5; N = 1500
x0, x1, y0, y1 = 90, 242, -128, 126
s = Image.open('data/optus/sat.png').convert('RGB').crop((int((x0 + N) / R), int((N - y1) / R), int((x1 + N) / R), int((N - y0) / R)))
a = np.asarray(s).astype(np.float32) / 255
L = a.mean(2)
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
th = white_tophat(ndi.gaussian_filter(L, 0.8), disk(int(4 / R)))   # lines brighter than their 8 m neighbourhood
pav = (a[..., 0] > a[..., 1] * 1.05) | (L > 0.6)   # paving (pinkish or light), not trees/grass
m = (th > TH) & pav
m = ndi.binary_closing(m, iterations=1)
m = remove_small_objects(m, int(6 / R ** 2))
sk = skeletonize(m)
kk = np.ones((3, 3), np.int8); kk[1, 1] = 0
for _ in range(int(3 / R)):
    nb = ndi.convolve(sk.astype(np.int8), kk, mode='constant'); sk = sk & (nb >= 2)
lab, n = ndi.label(sk, np.ones((3, 3)))
sz = ndi.sum(sk, lab, range(1, n + 1)); sk = np.isin(lab, 1 + np.nonzero(sz * R >= 6)[0])
lab, n = ndi.label(sk, np.ones((3, 3)))
np.save('_rib_sk.npy', sk)
o = np.asarray(s).copy(); o[ndi.binary_dilation(sk)] = (255, 0, 0)
big = Image.new('RGB', (s.size[0] * 2 + 10, s.size[1]), (0, 0, 0)); big.paste(s, (0, 0)); big.paste(Image.fromarray(o), (s.size[0] + 10, 0))
big.resize((big.size[0] * 2, big.size[1] * 2), Image.NEAREST).save('_rib_diag.png')
print('ribbon pieces', n, 'length m', round(float(sk.sum() * R)))
