"""Reference only (never on a model): straight-down Esri World Imagery around a ground, resampled to the scene frame
(x east, y north, metres, origin = spec lat/lon). usage: sat_fetch.py spec.json half_m m_per_px -> data/<g>/sat.png"""
import sys, os, json, math, io, time, urllib.request
import numpy as np
from PIL import Image
spec = json.load(open(sys.argv[1])); R = float(sys.argv[2]); S = float(sys.argv[3]); Z = 18
lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', spec['name'], 'sat2_tiles'); os.makedirs(D, exist_ok=True)
def tile_xy(lat, lon):
    n = 2 ** Z; return ((lon + 180) / 360 * n * 256, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256)
N = int(2 * R / S)
xs = (np.arange(N) + 0.5) * S - R; ys = R - (np.arange(N) + 0.5) * S
LON = lon0 + xs / KX; LAT = lat0 + ys / KY
n = 2 ** Z
PX = (LON + 180) / 360 * n * 256
PY = (1 - np.arcsinh(np.tan(np.radians(LAT))) / np.pi) / 2 * n * 256
tx0, tx1 = int(PX.min() // 256), int(PX.max() // 256); ty0, ty1 = int(PY.min() // 256), int(PY.max() // 256)
mos = Image.new('RGB', ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        p = os.path.join(D, f'{Z}_{tx}_{ty}.jpg')
        if not os.path.exists(p):
            for i in range(4):
                try:
                    r = urllib.request.urlopen(urllib.request.Request(f'https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={Z}', headers={'User-Agent': 'scene-reference/0.1'}), timeout=60).read()
                    open(p, 'wb').write(r); break
                except Exception as e: print('retry', e); time.sleep(3)
        mos.paste(Image.open(p).convert('RGB'), ((tx - tx0) * 256, (ty - ty0) * 256))
M = np.asarray(mos)
u = np.clip((PX - tx0 * 256).astype(int), 0, M.shape[1] - 1); v = np.clip((PY - ty0 * 256).astype(int), 0, M.shape[0] - 1)
out = M[v[:, None], u[None, :]]
Image.fromarray(out).save(os.path.join(os.path.dirname(D), 'sat2.png'))
json.dump({'half_m': R, 'm_per_px': S}, open(os.path.join(os.path.dirname(D), 'sat2.json'), 'w'))
print('SAT', N, 'px', (tx1 - tx0 + 1) * (ty1 - ty0 + 1), 'tiles')
