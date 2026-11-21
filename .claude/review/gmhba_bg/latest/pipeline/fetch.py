"""Fetch terrain tiles (AWS terrarium) and OSM (Overpass) around a ground.
usage: fetch.py name lat lon osm_radius_m
"""
import sys, os, math, json, urllib.request, urllib.parse, time
name, lat, lon, rad = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', name)
os.makedirs(os.path.join(out, 'tiles'), exist_ok=True)
UA = {'User-Agent': 'stadium-scene-prototype/0.1'}

def get(url, data=None):
    for i in range(4):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:
            print('retry', url[:80], e); time.sleep(5 * (i + 1))
    raise SystemExit('failed ' + url)

def tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

# terrain: z12 over +-30 km, z14 over +-3 km
for z, km in ((12, 30), (14, 3)):
    dlat = km / 111.0; dlon = km / (111.0 * math.cos(math.radians(lat)))
    x0, y0 = tile(lat + dlat, lon - dlon, z); x1, y1 = tile(lat - dlat, lon + dlon, z)
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            p = os.path.join(out, 'tiles', f'{z}_{x}_{y}.png')
            if not os.path.exists(p):
                open(p, 'wb').write(get(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'))
print('tiles done')

q = f"""[out:json][timeout:300];
(
 way["building"](around:{rad},{lat},{lon});
 way["landuse"](around:{rad},{lat},{lon});
 way["leisure"](around:{rad},{lat},{lon});
 way["natural"](around:{rad},{lat},{lon});
 relation["natural"="water"](around:{rad},{lat},{lon});
 way["waterway"](around:{rad},{lat},{lon});
 way["natural"="coastline"](around:{rad},{lat},{lon});
 way["highway"](around:{rad},{lat},{lon});
 way["railway"](around:{rad},{lat},{lon});
 node["natural"="tree"](around:{rad},{lat},{lon});
);
out geom tags;"""
p = os.path.join(out, 'osm.json')
if not os.path.exists(p):
    d = get('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data': q}).encode())
    open(p, 'wb').write(d)
js = json.load(open(p, encoding='utf-8'))
print('osm elements', len(js['elements']), os.path.getsize(p))
