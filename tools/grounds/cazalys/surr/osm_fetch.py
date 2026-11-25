"""Fetch OpenStreetMap data round Cazaly's from the OSM API (Overpass is not reachable from the build
machine), splitting a tile in four whenever the API refuses it as too big.

    python3 tools/grounds/cazalys/surr/osm_fetch.py <out dir> <half span m> <tile m>

Writes <out dir>/<lat>_<lon>_<size>.osm. Map data (c) OpenStreetMap contributors, ODbL."""
import math, os, sys, time, urllib.request, urllib.error

LAT0, LON0 = -16.935653, 145.749062


def get(out, a, b, c, d, depth=0):
    p = os.path.join(out, "%.5f_%.5f_%.5f_%.5f.osm" % (a, b, c, d))
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (a, b, c, d)
    for k in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ground-surroundings-builder/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            open(p, "wb").write(data)
            print("ok", depth, p, len(data), flush=True)
            return
        except urllib.error.HTTPError as e:
            if e.code == 400 and depth < 6:   # too many nodes: split
                mx, my = (a + c) / 2, (b + d) / 2
                for q in ((a, b, mx, my), (mx, b, c, my), (a, my, mx, d), (mx, my, c, d)):
                    get(out, *q, depth=depth + 1)
                return
            print("http", e.code, url, flush=True); time.sleep(5 * (k + 1))
        except Exception as e:
            print("err", e, url, flush=True); time.sleep(5 * (k + 1))


if __name__ == "__main__":
    out, half, tile = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    os.makedirs(out, exist_ok=True)
    dlat = 1 / 110574.0; dlon = 1 / (111320.0 * math.cos(math.radians(LAT0)))
    n = int(math.ceil(2 * half / tile))
    for i in range(n):
        for j in range(n):
            e0, n0 = -half + i * tile, -half + j * tile
            get(out, LON0 + e0 * dlon, LAT0 + n0 * dlat, LON0 + (e0 + tile) * dlon, LAT0 + (n0 + tile) * dlat)
