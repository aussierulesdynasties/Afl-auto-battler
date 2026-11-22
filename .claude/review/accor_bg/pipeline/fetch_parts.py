"""Fetch OSM building:part ways (real tower heights, min_height) around a ground. fetch_parts.py name radius_m"""
import sys, os, json, urllib.request, urllib.parse
name, rad = sys.argv[1], float(sys.argv[2])
here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, 'spec', name + '.json')))
lat, lon = spec['lat'], spec['lon']
q = f"""[out:json][timeout:300];
(
 way["building:part"](around:{rad},{lat},{lon});
 relation["building"]["type"="building"](around:{rad},{lat},{lon});
);
out geom tags;"""
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'stadium-scene-prototype/0.1'})
d = urllib.request.urlopen(req, timeout=300).read()
p = os.path.join(here, 'data', name, 'osm_parts.json')
open(p, 'wb').write(d)
js = json.loads(d)
print('parts', sum(1 for e in js['elements'] if e['type'] == 'way'), 'relations', sum(1 for e in js['elements'] if e['type'] == 'relation'))
