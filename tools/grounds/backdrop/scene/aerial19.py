"""Close straight-down aerial (Esri World Imagery z19, ~0.25 m a pixel; SAT_RELEASE = a Wayback release for a
closed ground's era), resampled to the scene frame (x east, y north, metres). Reference only: callers read colours
and positions from it, never put its pixels in the scene. Tiles cache in data/<g>/sat19[_release]/."""
import os, math, time, urllib.request
import numpy as np
from PIL import Image
def setup(spec, D):
    global lat0, lon0, KX, KY, NEAR, Z, S, REL, TD, URL, n2
    lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
    NEAR = spec.get('near_half_m', 1500)
    Z = 19; S = 0.25   # tile zoom; resample step (m)
    REL = os.environ.get('SAT_RELEASE', '')
    TD = os.path.join(D, 'sat19' + ('_' + REL if REL else '')); os.makedirs(TD, exist_ok=True)
    URL = ('https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/' + REL + '/{Z}/{ty}/{tx}') if REL else 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{ty}/{tx}'
    n2 = 2 ** Z * 256

def tile(tx, ty):
    p = os.path.join(TD, f'{Z}_{tx}_{ty}.jpg')
    if not os.path.exists(p):
        for i in range(4):
            try:
                r = urllib.request.urlopen(urllib.request.Request(URL.format(Z=Z, ty=ty, tx=tx), headers={'User-Agent': 'scene-reference/0.1'}), timeout=60).read()
                open(p, 'wb').write(r); break
            except Exception as e: print('retry', e); time.sleep(3)
    try: return np.asarray(Image.open(p).convert('RGB'))
    except Exception: return np.zeros((256, 256, 3), np.uint8)
def aerial(x0, y0, x1, y1):   # scene-frame metres -> image (rows north to south) at S m a pixel
    xs = np.arange(x0, x1, S) + S / 2; ys = np.arange(y1, y0, -S) - S / 2
    LON = lon0 + xs / KX; LAT = lat0 + ys / KY
    PX = (LON + 180) / 360 * n2; PY = (1 - np.arcsinh(np.tan(np.radians(LAT))) / np.pi) / 2 * n2
    tx0, tx1 = int(PX.min() // 256), int(PX.max() // 256); ty0, ty1 = int(PY.min() // 256), int(PY.max() // 256)
    M = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256, 3), np.uint8)
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            M[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = tile(tx, ty)
    u = np.clip((PX - tx0 * 256).astype(int), 0, M.shape[1] - 1); v = np.clip((PY - ty0 * 256).astype(int), 0, M.shape[0] - 1)
    return M[v[:, None], u[None, :]].astype(np.float32), xs, ys

