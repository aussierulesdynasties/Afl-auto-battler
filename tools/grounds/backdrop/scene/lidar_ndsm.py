"""Measured building heights from open LiDAR: height above bare ground (nDSM = DSM - DEM) on the ground's local metre
grid (x east, y north from the centre circle, rows north -> south like s2/), for prep.py's building heights.
Source: STAC collections of cloud-optimised GeoTIFFs, e.g. LINZ s3://nz-elevation (CC BY 4.0).
usage: lidar_ndsm.py ground lat lon dsm_collection_url dem_collection_url [half_m=1500] [step_m=1]
writes data/<ground>/bh.npy (float32 metres, NaN outside cover) + bh.json"""
import sys, os, json, urllib.request, numpy as np, rasterio
from concurrent.futures import ThreadPoolExecutor
from rasterio.windows import from_bounds
from pyproj import Transformer
from scipy.ndimage import map_coordinates
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
g, lat, lon, DSM, DEM = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5]
half = float(sys.argv[6]) if len(sys.argv) > 6 else 1500.0; step = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
KX = 111320 * np.cos(np.radians(lat)); KY = 110540
bb = [lon - half * 1.05 / KX, lat - half * 1.05 / KY, lon + half * 1.05 / KX, lat + half * 1.05 / KY]
def get(u): return json.load(urllib.request.urlopen(u, timeout=120))
def items(coll):
    c = get(coll); base = coll.rsplit('/', 1)[0] + '/'
    hrefs = [base + l['href'][2:] if l['href'].startswith('./') else l['href'] for l in c['links'] if l['rel'] == 'item']
    with ThreadPoolExecutor(16) as ex: its = list(ex.map(get, hrefs))
    out = []
    for h, it in zip(hrefs, its):
        b = it['bbox']
        if b[0] < bb[2] and b[2] > bb[0] and b[1] < bb[3] and b[3] > bb[1]:
            a = next(v for v in it['assets'].values() if v['href'].endswith(('.tif', '.tiff')))
            out.append(a['href'] if a['href'].startswith('http') else h.rsplit('/', 1)[0] + '/' + a['href'].lstrip('./'))
    return c, out
n = int(round(2 * half / step))
xs = -half + (np.arange(n) + 0.5) * step; ys = half - (np.arange(n) + 0.5) * step
def mosaic(coll):
    c, tifs = items(coll); print(c.get('title'), len(tifs), 'tiles')
    M = np.full((n, n), np.nan, np.float32)
    def one(u):
        with rasterio.open('/vsicurl/' + u) as src:
            tr = Transformer.from_crs(4326, src.crs, always_xy=True)
            out = np.full((n, n), np.nan, np.float32)
            for r0 in range(0, n, 500):   # row bands keep memory small
                GX, GY = np.meshgrid(xs, ys[r0:r0 + 500]); EX, EY = tr.transform(lon + GX / KX, lat + GY / KY)
                l, b, r, t = src.bounds; m = (EX >= l) & (EX < r) & (EY > b) & (EY <= t)
                if not m.any(): continue
                w = from_bounds(EX[m].min() - 2, EY[m].min() - 2, EX[m].max() + 2, EY[m].max() + 2, src.transform).round_offsets().round_lengths()
                A = src.read(1, window=w, boundless=True, fill_value=np.nan, masked=True).filled(np.nan).astype(np.float32)
                A[A < -1000] = np.nan   # nodata (sea)
                tt = src.window_transform(w); col = (EX - tt.c) / tt.a - 0.5; row = (EY - tt.f) / tt.e - 0.5
                v = map_coordinates(A, [row, col], order=1, mode='constant', cval=np.nan)
                out[r0:r0 + 500][m] = v[m]
            return out
    with ThreadPoolExecutor(8) as ex:
        for o in ex.map(one, tifs): M = np.where(np.isnan(M), o, M)
    return M, c
S, cs = mosaic(DSM); T, ct = mosaic(DEM)
H = S - T
W = os.path.join(os.environ.get('WORK', '/home/user/work'), 'proto', 'data', g)
np.save(os.path.join(W, 'bh.npy'), H.astype(np.float32))
json.dump({'half_m': half, 'm_per_px': step, 'rows': 'north to south', 'measured': True, 'kind': 'lidar nDSM',
           'source': '%s minus %s, %s' % (cs.get('title'), ct.get('title'), cs.get('license'))}, open(os.path.join(W, 'bh.json'), 'w'))
print('saved', H.shape, 'covered', round(float(np.isfinite(H).mean()), 3), 'p99', float(np.nanpercentile(H, 99)))
# the bare-earth DEM itself, for prep.py's measured land: data/<g>/dem/near.npy, turf at the centre circle = 0, rows south -> north
DD = os.path.join(W, 'dem'); os.makedirs(DD, exist_ok=True)
c = n // 2; z0 = float(np.nanmedian(T[c - 10:c + 10, c - 10:c + 10]))
np.save(os.path.join(DD, 'near.npy'), np.flipud(np.where(np.isfinite(T), T, 0.0) - z0)   # off the scan = the sea at datum 0
        .astype(np.float32))
json.dump({'half_m': half - step / 2, 'step_m': step, 'datum': 'turf at the centre circle = 0 (%.2f m above the DEM datum)' % z0,
           'rows': 'south to north', 'source': '%s, %s' % (ct.get('title'), ct.get('license'))}, open(os.path.join(DD, 'near.json'), 'w'))
print('dem near saved, centre', z0, 'range', float(np.nanmin(T - z0)), float(np.nanmax(T - z0)))
