"""The far land's real colours: Sentinel-2 (Digital Earth Australia ARD, CC BY 4.0, contains modified Copernicus
Sentinel data), median of clear footy-season scenes from each tile that covers the area, read from the files' overviews
at 80 m, on the ground's local metre grid (north up). Colours only: what a forest, a paddock or a suburb looks like
from kilometres off. usage: s2far.py ground lat lon [half_m] -> /home/user/work/s2/<ground>_far.npy (H, W, 3)
reflectance x 10000 (NaN where no clear view), + _far.json, + _far_water.npy (share of clear looks that saw water)"""
import sys, json, math, urllib.request, numpy as np, rasterio, os, collections
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from pyproj import Transformer
from scipy.ndimage import map_coordinates
g, lat, lon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); half = float(sys.argv[4]) if len(sys.argv) > 4 else 16000.0
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR'); os.environ.setdefault('AWS_NO_SIGN_REQUEST', 'YES')
KX = 111320 * math.cos(math.radians(lat)); KY = 110540
d = half * 1.05
bb = (lon - d / KX, lat - d / KY, lon + d / KX, lat + d / KY)
url = ('https://explorer.dea.ga.gov.au/stac/search?collections=ga_s2am_ard_3,ga_s2bm_ard_3,ga_s2cm_ard_3&bbox=%f,%f,%f,%f'
       '&datetime=2024-04-01/2026-11-20&limit=500') % bb
feats = json.load(urllib.request.urlopen(url, timeout=180))['features']
feats = [f for f in feats if (f['properties'].get('eo:cloud_cover') or 100) < 5 and int(f['properties']['datetime'][5:7]) in (4, 5, 6, 7, 8, 9)]
by = collections.defaultdict(list)
for f in feats: by[f['properties'].get('odc:region_code', f['id'][:12])].append(f)
pick = []
for k, fs in by.items(): fs.sort(key=lambda f: f['properties']['eo:cloud_cover']); pick += fs[:5]
print('tiles', list(by), 'scenes', len(pick))
step = 80.0; n = int(2 * half / step)
xs = -half + (np.arange(n) + 0.5) * step; ys = half - (np.arange(n) + 0.5) * step
GX, GY = np.meshgrid(xs, ys); LON = lon + GX / KX; LAT = lat + GY / KY
stack = []; wat = []
for f in pick:
    a = f['assets']; epsg = f['properties']['proj:epsg']
    tr = Transformer.from_crs(4326, epsg, always_xy=True); EX, EY = tr.transform(LON, LAT)
    bands = []
    try:
        for k in ('nbart_red', 'nbart_green', 'nbart_blue', 'oa_fmask'):
            href = a[k]['href'].replace('s3://dea-public-data/', 'https://dea-public-data.s3.ap-southeast-2.amazonaws.com/')
            with rasterio.open('/vsicurl/' + href) as src:
                w = from_bounds(EX.min() - 200, EY.min() - 200, EX.max() + 200, EY.max() + 200, src.transform)
                fac = step / abs(src.transform.a)
                oh, ow = max(1, int(w.height / fac)), max(1, int(w.width / fac))
                arr = src.read(1, window=w, boundless=True, fill_value=0, out_shape=(oh, ow),
                               resampling=Resampling.nearest if k == 'oa_fmask' else Resampling.average).astype(np.float32)
                t = src.window_transform(w); sx = w.width / ow; sy = w.height / oh
                col = (EX - t.c) / (t.a * sx) - 0.5; row = (EY - t.f) / (t.e * sy) - 0.5
                bands.append(map_coordinates(arr, [row, col], order=0 if k == 'oa_fmask' else 1, mode='constant', cval=0))
    except Exception as e:
        print('skip', f['id'], e); continue
    rgb = np.stack(bands[:3], -1); clear = (bands[3] == 1) & (rgb.min(-1) > 0)
    fm = bands[3]; wv = np.where((fm == 1) | (fm == 5), (fm == 5).astype(np.float32), np.nan); wat.append(wv)   # fmask 5: water
    rgb[~clear] = np.nan; stack.append(rgb); print(f['properties']['datetime'][:10], 'clear', round(float(clear.mean()), 3))
M = np.nanmedian(np.stack(stack), 0)
np.save(os.environ.get('WORK', '/home/user/work') + '/s2/%s_far.npy' % g, M.astype(np.float32))
np.save(os.environ.get('WORK', '/home/user/work') + '/s2/%s_far_water.npy' % g, np.nanmean(np.stack(wat), 0).astype(np.float32))   # share of clear looks that saw water
json.dump({'half_m': half, 'm_per_px': step, 'scenes': [f['id'] for f in pick],
           'source': 'Digital Earth Australia Sentinel-2 ARD (CC BY 4.0); contains modified Copernicus Sentinel data'}, open(os.environ.get('WORK', '/home/user/work') + '/s2/%s_far.json' % g, 'w'))
print('saved', M.shape, 'nan', int(np.isnan(M).any(-1).sum()))
