# z20 Esri World Imagery (reference only) over the Optus east plaza, resampled to world metres at 0.125 m/px.
import math, os, time, urllib.request, io, numpy as np
from PIL import Image
LAT, LON = -31.951064, 115.889206; X0, X1, Y0, Y1 = 80, 260, -50, 135; Z = 19; R = 0.125
TD = '../hires_tiles'
def ll(x, y):  # world metres -> lat/lon (local equirectangular, as the pipeline)
    return LAT + y / 110540.0, LON + x / (111320.0 * math.cos(math.radians(LAT)))
def px(lat, lon):
    n = 2 ** Z; s = math.sin(math.radians(lat))
    return (lon + 180) / 360 * n * 256, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n * 256
(la0, lo0), (la1, lo1) = ll(X0, Y1), ll(X1, Y0)
(gx0, gy0), (gx1, gy1) = px(la0, lo0), px(la1, lo1)
T = {}
for tx in range(int(gx0 // 256), int(gx1 // 256) + 1):
    for ty in range(int(gy0 // 256), int(gy1 // 256) + 1):
        p = os.path.join(TD, f'{Z}_{tx}_{ty}.jpg')
        if not os.path.exists(p):
            rq = urllib.request.Request(f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{ty}/{tx}', headers={'User-Agent': 'stadium-bg-ref/1.0'})
            open(p, 'wb').write(urllib.request.urlopen(rq, timeout=30).read()); time.sleep(0.2)
        T[(tx, ty)] = Image.open(p).convert('RGB')
W, H = int((X1 - X0) / R), int((Y1 - Y0) / R)
out = np.zeros((H, W, 3), np.uint8)
xs = X0 + (np.arange(W) + 0.5) * R; ys = Y1 - (np.arange(H) + 0.5) * R
for j, y in enumerate(ys):
    for i0 in range(0, W, 1):
        pass
# vectorised sampling
XX, YY = np.meshgrid(xs, ys); LA = LAT + YY / 110540.0; LO = LON + XX / (111320.0 * math.cos(math.radians(LAT)))
n = 2 ** Z; S = np.sin(np.radians(LA)); GX = (LO + 180) / 360 * n * 256; GY = (0.5 - np.log((1 + S) / (1 - S)) / (4 * np.pi)) * n * 256
tx0, ty0 = int(gx0 // 256), int(gy0 // 256); ntx, nty = int(gx1 // 256) - tx0 + 1, int(gy1 // 256) - ty0 + 1
mos = Image.new('RGB', (ntx * 256, nty * 256))
for (tx, ty), im in T.items(): mos.paste(im, ((tx - tx0) * 256, (ty - ty0) * 256))
M = np.asarray(mos); u = np.clip((GX - tx0 * 256).astype(int), 0, M.shape[1] - 1); v = np.clip((GY - ty0 * 256).astype(int), 0, M.shape[0] - 1)
Image.fromarray(M[v, u]).save('data/optus/sat_hi_plaza.png'); print('tiles', len(T), 'size', W, H)
