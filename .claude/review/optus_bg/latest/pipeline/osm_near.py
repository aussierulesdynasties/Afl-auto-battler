"""List OSM ways/relations with a node within R m of (x, y) in the scene frame. osm_near.py g x y R"""
import sys, json, math
g = sys.argv[1]; X, Y, R = map(float, sys.argv[2:5])
d = json.load(open(f'data/{g}/osm.json', encoding='utf-8'))
spec = json.load(open(f"spec/{g}.json"))
lat0, lon0 = spec["lat"], spec["lon"]
if False:
    pass
KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
def xy(lat, lon):
    return ((lon - lon0) * KX, (lat - lat0) * KY)
nodes = {}
for e in d['elements']:
    if e['type'] == 'node':
        nodes[e['id']] = xy(e['lat'], e['lon'])
for e in d['elements']:
    if e['type'] != 'way':
        continue
    pts = [xy(p['lat'], p['lon']) for p in e.get('geometry', [])]
    if any((p[0] - X) ** 2 + (p[1] - Y) ** 2 < R * R for p in pts):
        t = e.get('tags', {})
        print(e['id'], {k_: v for k_, v in t.items() if k_ in ('highway', 'leisure', 'building', 'landuse', 'natural', 'waterway', 'surface', 'name', 'sport', 'man_made', 'amenity', 'footway', 'layer', 'tunnel', 'covered')})
