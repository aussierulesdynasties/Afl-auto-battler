"""Fetch the open data data.py and build_bpy.py read, +-1.9 km round Mars Stadium (and terrain to 30 km):

    python3 tools/grounds/mars/surrounds/fetch.py WORK_DIR

WORK_DIR/osm/t??.osm   OpenStreetMap API map calls, a 4 x 4 grid of tiles (ODbL)
WORK_DIR/chm.npy       Meta/WRI 1 m canopy height window (CC BY 4.0), needs rasterio
WORK_DIR/dem/          AWS Terrain Tiles (terrarium): z12 to +-30 km, z14 to +-3 km
Nothing fetched here is committed; the outputs data.py and build_bpy.py derive from it are.
"""
import math, os, sys, time, urllib.request
import numpy as np

LAT0, LON0 = -37.539307, 143.848166
UA = {'User-Agent': 'afl-ground-builder/1.0'}


def get(url):
    for k in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except Exception as e:
            print('retry', url[:90], e); time.sleep(5 * (k + 1))
    raise SystemExit('failed ' + url)


def osm(d, km=1.8, n=4):
    os.makedirs(d, exist_ok=True)
    dlat = km / 111.0; dlon = km / (111.0 * math.cos(math.radians(LAT0)))
    for i in range(n):
        for j in range(n):
            a, b = LON0 - dlon + 2 * dlon * i / n, LON0 - dlon + 2 * dlon * (i + 1) / n
            c, e = LAT0 - dlat + 2 * dlat * j / n, LAT0 - dlat + 2 * dlat * (j + 1) / n
            p = os.path.join(d, f't{i}{j}.osm')
            if not os.path.exists(p):
                open(p, 'wb').write(get(f'https://api.openstreetmap.org/api/0.6/map?bbox={a:.5f},{c:.5f},{b:.5f},{e:.5f}'))


def chm(p, half=1900.0):
    import rasterio
    from rasterio.windows import from_bounds
    z = 9; n = 2 ** z
    x = int((LON0 + 180) / 360 * n); y = int((1 - math.asinh(math.tan(math.radians(LAT0))) / math.pi) / 2 * n)
    q = ''.join(str(((x >> (i - 1)) & 1) + 2 * ((y >> (i - 1)) & 1)) for i in range(z, 0, -1))
    R = 6378137.0; mx = math.radians(LON0) * R; my = R * math.log(math.tan(math.pi / 4 + math.radians(LAT0) / 2))
    h = half / math.cos(math.radians(LAT0))
    with rasterio.open(f'/vsicurl/https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/{q}.tif') as ds:
        np.save(p, ds.read(1, window=from_bounds(mx - h, my - h, mx + h, my + h, ds.transform)))


def dem(d):
    os.makedirs(d, exist_ok=True)
    def tile(lat, lon, z):
        n = 2 ** z; return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    for z, km in ((12, 30), (14, 3)):
        dlat = km / 111.0; dlon = km / (111.0 * math.cos(math.radians(LAT0)))
        x0, y0 = tile(LAT0 + dlat, LON0 - dlon, z); x1, y1 = tile(LAT0 - dlat, LON0 + dlon, z)
        for x in range(int(x0), int(x1) + 1):
            for y in range(int(y0), int(y1) + 1):
                p = os.path.join(d, f'{z}_{x}_{y}.png')
                if not os.path.exists(p):
                    open(p, 'wb').write(get(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'))


if __name__ == '__main__':
    w = sys.argv[1]
    osm(os.path.join(w, 'osm')); dem(os.path.join(w, 'dem')); chm(os.path.join(w, 'chm.npy'))
