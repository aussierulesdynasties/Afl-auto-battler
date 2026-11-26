"""Sentinel-2 colours for grounds outside Digital Earth Australia's cover (New Zealand, China): Copernicus Sentinel-2 L2A
from Element 84's Earth Search (open data on AWS; contains modified Copernicus Sentinel data). Same outputs as s2.py and
s2far.py: median of clear footy-season looks, reflectance x 10000, on the ground's local metre grid (north up).
usage: s2es.py near|far ground lat lon [half_m] [months]
  near -> s2/<ground>.npy (10 m, default half 1500)   far -> s2/<ground>_far.npy + _far_water.npy (80 m, default 16 km)
  months: comma list, default 4-9 (southern footy season); Shanghai's game is in autumn/spring, pass e.g. 3,4,5,10,11"""
import sys, json, math, urllib.request, numpy as np, rasterio, os, collections
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from pyproj import Transformer
from scipy.ndimage import map_coordinates
mode, g, lat, lon = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
far = mode == 'far'
half = float(sys.argv[5]) if len(sys.argv) > 5 else (16000.0 if far else 1500.0)
months = [int(m) for m in sys.argv[6].split(',')] if len(sys.argv) > 6 else [4, 5, 6, 7, 8, 9]
step = 80.0 if far else 10.0
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR'); os.environ.setdefault('AWS_NO_SIGN_REQUEST', 'YES')
os.environ.setdefault('GDAL_HTTP_MULTIRANGE', 'YES'); os.environ.setdefault('GDAL_HTTP_MERGE_CONSECUTIVE_RANGES', 'YES')
KX = 111320 * math.cos(math.radians(lat)); KY = 110540
d = half * 1.05
bb = [lon - d / KX, lat - d / KY, lon + d / KX, lat + d / KY]
feats = []
body = {'collections': ['sentinel-2-l2a'], 'bbox': bb, 'datetime': '2023-01-01T00:00:00Z/2026-11-20T00:00:00Z', 'limit': int(os.environ.get('ES_LIMIT', 500)),
        'query': {'eo:cloud_cover': {'lt': 30}}}
req = urllib.request.Request('https://earth-search.aws.element84.com/v1/search', json.dumps(body).encode(),
                             {'Content-Type': 'application/json'})
for _try in range(5):
    try: feats = json.load(urllib.request.urlopen(req, timeout=180))['features']; break
    except Exception as e: print('search retry', e); import time; time.sleep(20 * (_try + 1))
feats = [f for f in feats if int(f['properties']['datetime'][5:7]) in months]
by = collections.defaultdict(list)
for f in feats: by[f['properties'].get('grid:code', f['id'][4:9])].append(f)
pick = []
for k, fs in by.items(): fs.sort(key=lambda f: f['properties']['eo:cloud_cover']); pick += fs[:(8 if far else 12)]
print('tiles', list(by), 'scenes', len(pick))
n = int(2 * half / step)
xs = -half + (np.arange(n) + 0.5) * step; ys = half - (np.arange(n) + 0.5) * step
GX, GY = np.meshgrid(xs, ys); LON = lon + GX / KX; LAT = lat + GY / KY
stack = []; wat = []
for f in pick:
    a = f['assets']; p = f['properties']; epsg = p.get('proj:epsg') or int(str(p.get('proj:code', '')).split(':')[-1])
    off = 1000.0 if float(p.get('s2:processing_baseline', '0') or 0) >= 4.0 and not p.get('earthsearch:boa_offset_applied') else 0.0   # baseline 04.00 adds 1000 unless Earth Search took it off
    tr = Transformer.from_crs(4326, epsg, always_xy=True); EX, EY = tr.transform(LON, LAT)
    bands = []
    try:
        for k in ('red', 'green', 'blue', 'scl'):
            with rasterio.open('/vsicurl/' + a[k]['href']) as src:
                w = from_bounds(EX.min() - 200, EY.min() - 200, EX.max() + 200, EY.max() + 200, src.transform)
                fac = max(1.0, step / abs(src.transform.a))
                oh, ow = max(1, int(w.height / fac)), max(1, int(w.width / fac))
                arr = src.read(1, window=w, boundless=True, fill_value=0, out_shape=(oh, ow),
                               resampling=Resampling.nearest if k == 'scl' else Resampling.average).astype(np.float32)
                t = src.window_transform(w); sx = w.width / ow; sy = w.height / oh
                col = (EX - t.c) / (t.a * sx) - 0.5; row = (EY - t.f) / (t.e * sy) - 0.5
                bands.append(map_coordinates(arr, [row, col], order=0 if k == 'scl' else 1, mode='constant', cval=0))
    except Exception as e:
        print('skip', f['id'], e); continue
    rgb = np.stack(bands[:3], -1) - off; s = bands[3]
    clear = np.isin(s, (4, 5, 6, 7, 11)) & (rgb.min(-1) > 0)      # vegetation, bare, water, unclassified, snow
    wat.append(np.where(np.isin(s, (4, 5, 6, 7)), (s == 6).astype(np.float32), np.nan))
    rgb[~clear] = np.nan; stack.append(rgb); print(p['datetime'][:10], 'clear', round(float(clear.mean()), 3))
M = np.nanmedian(np.stack(stack), 0)
W = os.environ.get('WORK', '/home/user/work') + '/s2/'
src = 'Copernicus Sentinel-2 L2A via Earth Search (open data); contains modified Copernicus Sentinel data'
if far:
    np.save(W + '%s_far.npy' % g, M.astype(np.float32))
    np.save(W + '%s_far_water.npy' % g, np.nanmean(np.stack(wat), 0).astype(np.float32))
    json.dump({'half_m': half, 'm_per_px': step, 'scenes': [f['id'] for f in pick], 'source': src}, open(W + '%s_far.json' % g, 'w'))
else:
    np.save(W + '%s.npy' % g, M.astype(np.float32))
    json.dump({'half_m': half, 'm_per_px': step, 'scenes': [f['id'] for f in pick],
               'dates': [f['properties']['datetime'][:10] for f in pick], 'source': src}, open(W + '%s.json' % g, 'w'))
print('saved', M.shape, 'nan', int(np.isnan(M).any(-1).sum()))
