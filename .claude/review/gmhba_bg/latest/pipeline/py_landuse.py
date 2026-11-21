"""Land-use mask traced from the 60 km reference aerial (data/gmhba/sat_far.png, 30 m/px, never on a model):
0 farm, 1 urban, 2 forest, 3 water. Saves data/gmhba/landuse.npy (2000x2000, row 0 = north) and a preview."""
import os, sys, numpy as np
from PIL import Image, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, 'data', 'gmhba')
a = np.asarray(Image.open(os.path.join(D, 'sat_far.png'))).astype(np.float32)
L = a.mean(2); S = a.max(2) - a.min(2)
def box(x, r):
    k = 2 * r + 1; p = np.pad(x.astype(np.float64), r, mode='edge'); c = p.cumsum(0).cumsum(1); c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
sd = np.sqrt(np.maximum(box(L * L, 2) - box(L, 2) ** 2, 0))
water = (a[..., 2] > a[..., 0] + 4) & (L < 90) & (sd < 8)
forest = (L < 62) & (a[..., 1] >= a[..., 0] - 2) & ~water
urban = np.load(os.path.join(D, 'urban_osm.npy')) & ~water   # urban extent from OSM land-use polygons
lu = np.zeros(L.shape, np.uint8); lu[urban] = 1; lu[forest] = 2; lu[water] = 3
for k in (2,):   # majority clean-up: keep classes that cover >45% of a 270 m window
    m = box((lu == k).astype(np.float32), 4) > 0.45; lu[(lu == k) & ~m] = 0; lu[(lu == 0) & m] = k
np.save(os.path.join(D, 'landuse.npy'), lu)
pal = np.array([(170, 150, 100), (128, 128, 136), (40, 80, 40), (30, 60, 110)], np.uint8)
Image.fromarray(pal[lu]).resize((1000, 1000)).save(sys.argv[1])
print('landuse farm/urban/forest/water %', [round(float((lu == k).mean() * 100), 1) for k in range(4)])
