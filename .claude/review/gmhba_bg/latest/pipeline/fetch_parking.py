"""Add OSM car parks (way amenity=parking) to data/<name>/osm.json; fetch.py's query left them out. usage: fetch_parking.py name"""
import sys, os, json, shutil, urllib.request, urllib.parse
H = os.path.dirname(os.path.abspath(__file__)); name = sys.argv[1]
spec = json.load(open(os.path.join(H, 'spec', name + '.json'))); lat, lon = spec['lat'], spec['lon']; rad = 2200
p = os.path.join(H, 'data', name, 'osm.json'); bk = p + '.bak_noparking'
if not os.path.exists(bk): shutil.copy(p, bk)
q = f'[out:json][timeout:180];(way["amenity"="parking"](around:{rad},{lat},{lon}););out geom tags;'
req = urllib.request.Request('https://overpass-api.de/api/interpreter', urllib.parse.urlencode({'data': q}).encode(), {'User-Agent': 'stadium-scene-prototype/0.1'})
new = json.loads(urllib.request.urlopen(req, timeout=200).read())['elements']
js = json.load(open(p, encoding='utf-8')); have = {(e['type'], e['id']) for e in js['elements']}
add = [e for e in new if (e['type'], e['id']) not in have]
js['elements'] += add; json.dump(js, open(p, 'w', encoding='utf-8'))
print('car parks fetched', len(new), 'added', len(add))
