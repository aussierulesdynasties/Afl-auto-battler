# Satellite tiles (Google by default, 'src': 'esri' for Esri World Imagery), z19 -> a 0.25 m/px north-up mosaic of +-HALF m round the ground's origin: work/sat.png
# python3 kit/sat.py tools/grounds/<slug>   (origin lat/lon and half from <slug>.json)
import sys, os, math, json, urllib.request, numpy as np, cv2
G = os.path.abspath(sys.argv[1]); SLUG = os.path.basename(G); D = json.load(open(os.path.join(G, 'model', SLUG + '.json')))
LAT0, LON0 = D['lat'], D['lon']; HALF = D.get('half', 260); RES = 0.25; Z = int(D.get('zoom', 19)); N = 2 ** Z
p = math.radians(LAT0); MLAT = 111132.92 - 559.82 * math.cos(2 * p) + 1.175 * math.cos(4 * p); MLON = 111412.84 * math.cos(p) - 93.5 * math.cos(3 * p)
def tile_xy(lat, lon):
    return (lon + 180) / 360 * N, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * N
tx0, ty0 = tile_xy(LAT0 + HALF / MLAT, LON0 - HALF / MLON); tx1, ty1 = tile_xy(LAT0 - HALF / MLAT, LON0 + HALF / MLON)
X0, Y0, X1, Y1 = int(tx0), int(ty0), int(tx1), int(ty1)
TD = os.path.join(G, 'work', 'tiles'); os.makedirs(TD, exist_ok=True)
big = np.zeros(((Y1 - Y0 + 1) * 256, (X1 - X0 + 1) * 256, 3), np.uint8)
for ty in range(Y0, Y1 + 1):
    for tx in range(X0, X1 + 1):
        src = D.get('src', 'google'); f = os.path.join(TD, f'{src}{Z}_{tx}_{ty}.jpg')
        if not os.path.exists(f):
            u = (f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{ty}/{tx}' if src == 'esri'
                 else f'https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={Z}')
            rq = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            open(f, 'wb').write(urllib.request.urlopen(rq, timeout=30).read())
        big[(ty - Y0) * 256:(ty - Y0 + 1) * 256, (tx - X0) * 256:(tx - X0 + 1) * 256] = cv2.imread(f)
n = int(2 * HALF / RES); xs = -HALF + (np.arange(n) + 0.5) * RES; ys = HALF - (np.arange(n) + 0.5) * RES
X, Y = np.meshgrid(xs, ys); lat = LAT0 + Y / MLAT; lon = LON0 + X / MLON
mx = ((lon + 180) / 360 * N - X0) * 256; my = ((1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * N - Y0) * 256
out = cv2.remap(big, mx.astype(np.float32) - 0.5, my.astype(np.float32) - 0.5, cv2.INTER_CUBIC)
cv2.imwrite(os.path.join(G, 'work', 'sat.png'), out); print(out.shape, (X1 - X0 + 1) * (Y1 - Y0 + 1), 'tiles')
