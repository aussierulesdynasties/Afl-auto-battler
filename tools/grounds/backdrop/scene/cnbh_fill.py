"""Building heights for grounds in China, where Overture's footprints carry almost none: CNBH-10 m (Wu et al. 2023,
Zenodo 7827315, CC BY 4.0), a 10 m building-height raster for China. Each footprint without a height takes the 75th
percentile of the raster's pixels inside it (its centre pixel when it is smaller than one). Writes the heights back
into overture/<ground>.json with src_height 'CNBH-10m'.
usage: cnbh_fill.py ground tile_name   e.g. cnbh_fill.py jiangwan CNBH10m_X121Y31.tif"""
import sys, json, os, numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from shapely import wkt as W
from shapely.ops import transform as T
from pyproj import Transformer
from scipy import ndimage
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
g, tile = sys.argv[1], sys.argv[2]
P = os.path.join(os.environ.get('WORK', '/home/user/work'), 'overture', g + '.json')
B = json.load(open(P))
src = rasterio.open('/vsicurl/https://zenodo.org/records/7827315/files/' + tile)
tr = Transformer.from_crs(4326, src.crs, always_xy=True)
geo = [T(tr.transform, W.loads(b['wkt'])) for b in B]
xs = [q.bounds for q in geo]
x0 = min(b[0] for b in xs) - 50; y0 = min(b[1] for b in xs) - 50; x1 = max(b[2] for b in xs) + 50; y1 = max(b[3] for b in xs) + 50
win = from_bounds(x0, y0, x1, y1, src.transform).round_offsets().round_lengths()
H = src.read(1, window=win, boundless=True, fill_value=0).astype(np.float32); wt = src.window_transform(win)
print('raster', H.shape, 'max', float(H.max()))
need = [i for i, b in enumerate(B) if not b.get('height')]
lab = rasterize(((geo[i], k + 1) for k, i in enumerate(need)), out_shape=H.shape, transform=wt, fill=0, dtype='int32')
got = 0
idx = np.arange(1, len(need) + 1)
p75 = ndimage.labeled_comprehension(H, lab, idx, lambda v: np.percentile(v[v > 0], 75) if (v > 0).any() else 0.0, np.float32, 0.0)
inv = ~wt
for k, i in enumerate(need):
    h = float(p75[k])
    if h <= 0:   # smaller than a pixel: the pixel under its centre
        c = geo[i].centroid; cc, rr = inv * (c.x, c.y)
        rr, cc = int(rr), int(cc)
        if 0 <= rr < H.shape[0] and 0 <= cc < H.shape[1]: h = float(H[rr, cc])
    if h > 0:
        B[i]['height'] = round(h, 1); B[i]['src_height'] = 'CNBH-10m'; got += 1
json.dump(B, open(P, 'w'))
hs = np.array([b['height'] for b in B if b.get('height')])
print(g, 'heights filled', got, 'of', len(need), '; over 30 m', int((hs > 30).sum()), 'max', float(hs.max()))
