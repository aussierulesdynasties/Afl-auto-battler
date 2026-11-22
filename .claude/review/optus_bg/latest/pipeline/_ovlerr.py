# overlay error: distance from each traced polygon edge point to the nearest raw tone edge in the z19 aerial (classes before generalisation)
import json, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color
R = 0.125; AX0, AY1 = 80, 135
im = np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')).astype(np.float32) / 255
lab = color.rgb2lab(ndi.gaussian_filter(im, (4, 4, 0)))
c = np.where(lab[..., 1] > 8, 0, np.where(lab[..., 0] > 70, 1, 2))
c = ndi.median_filter(c, 9)
edge = (ndi.grey_dilation(c, 3) != ndi.grey_erosion(c, 3))
dist = ndi.distance_transform_edt(~edge) * R
O = np.array(json.load(open('spec/optus_fc_hand.json'))['outline'])
from matplotlib.path import Path
inside = Path(O)
e = []
for b in json.load(open('spec/optus_fc_hand.json'))['bands']:
    p = np.array(b['pts'])
    for (x0, y0), (x1, y1) in zip(p, np.roll(p, -1, 0)):
        for t in np.linspace(0, 1, 6, endpoint=False):
            x, y = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
            if not inside.contains_point((x, y)) or ((x + 16) / 143) ** 2 + (y / 128) ** 2 < 1: continue
            j, r = int((x - AX0) / R), int((AY1 - y) / R)
            if 0 <= r < dist.shape[0] and 0 <= j < dist.shape[1]: e.append(dist[r, j])
e = np.array(e); print('overlay error (band edges inside plaza outline): n %d, median %.2f m, mean %.2f m, p90 %.2f m, max %.2f m' % (len(e), np.median(e), e.mean(), np.percentile(e, 90), e.max()))
