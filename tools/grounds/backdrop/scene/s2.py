"""Sentinel-2 colours round a ground from Digital Earth Australia's analysis-ready data (CC BY 4.0, contains modified
Copernicus Sentinel data). Median of clear footy-season scenes, 10 m, on the ground's local metre grid (north up).
usage: s2.py ground lat lon [half_m]   -> /home/user/work/s2/<ground>.npy  (H, W, 3) reflectance x 10000, + .json"""
import sys, json, math, urllib.request, numpy as np, rasterio, os
from rasterio.windows import from_bounds
from pyproj import Transformer
g, lat, lon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); half = float(sys.argv[4]) if len(sys.argv) > 4 else 1500.0
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR'); os.environ.setdefault('AWS_NO_SIGN_REQUEST', 'YES')
KX = 111320 * math.cos(math.radians(lat)); KY = 110540
d = half * 1.1
bb = (lon - d / KX, lat - d / KY, lon + d / KX, lat + d / KY)
url = ('https://explorer.dea.ga.gov.au/stac/search?collections=ga_s2am_ard_3,ga_s2bm_ard_3,ga_s2cm_ard_3&bbox=%f,%f,%f,%f'
       '&datetime=2024-04-01/2026-11-20&limit=300') % bb
feats = json.load(urllib.request.urlopen(url, timeout=120))['features']
feats = [f for f in feats if (f['properties'].get('eo:cloud_cover') or 100) < 3 and int(f['properties']['datetime'][5:7]) in (4, 5, 6, 7, 8, 9)]
feats.sort(key=lambda f: f['properties']['eo:cloud_cover']); feats = feats[:10]
print('scenes', len(feats), [f['properties']['datetime'][:10] for f in feats])
step = 10.0; n = int(2 * half / step)
xs = -half + (np.arange(n) + 0.5) * step; ys = half - (np.arange(n) + 0.5) * step
GX, GY = np.meshgrid(xs, ys); LON = lon + GX / KX; LAT = lat + GY / KY
stack = []
for f in feats:
    a = f['assets']; epsg = f['properties']['proj:epsg']
    tr = Transformer.from_crs(4326, epsg, always_xy=True); EX, EY = tr.transform(LON, LAT)
    bands = []
    for k in ('nbart_red', 'nbart_green', 'nbart_blue', 'oa_fmask'):
        href = a[k]['href'].replace('s3://dea-public-data/', 'https://dea-public-data.s3.ap-southeast-2.amazonaws.com/')
        with rasterio.open('/vsicurl/' + href) as src:
            w = from_bounds(EX.min() - 30, EY.min() - 30, EX.max() + 30, EY.max() + 30, src.transform)
            arr = src.read(1, window=w, boundless=True, fill_value=0).astype(np.float32); t = src.window_transform(w)
            col = (EX - t.c) / t.a; row = (EY - t.f) / t.e
            from scipy.ndimage import map_coordinates
            bands.append(map_coordinates(arr, [row, col], order=0 if k == 'oa_fmask' else 1, mode='nearest'))
    rgb = np.stack(bands[:3], -1); clear = (bands[3] == 1) & (rgb.min(-1) > 0)
    rgb[~clear] = np.nan; stack.append(rgb); print(f['properties']['datetime'][:10], 'clear', round(float(clear.mean()), 3))
M = np.nanmedian(np.stack(stack), 0)
np.save(os.environ.get('WORK', '/home/user/work') + '/s2/%s.npy' % g, M.astype(np.float32))
json.dump({'half_m': half, 'm_per_px': step, 'scenes': [f['id'] for f in feats], 'dates': [f['properties']['datetime'][:10] for f in feats],
           'source': 'Digital Earth Australia Sentinel-2 ARD (CC BY 4.0); contains modified Copernicus Sentinel data'}, open(os.environ.get('WORK', '/home/user/work') + '/s2/%s.json' % g, 'w'))
print('saved', M.shape, 'nan', int(np.isnan(M).any(-1).sum()))
