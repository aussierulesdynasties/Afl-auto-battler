"""Add landuse/leisure/natural multipolygon relations (parklands, golf courses) to data/<name>/osm.json. fetch_rel.py name radius_m"""
import sys, os, json, urllib.request, urllib.parse, shutil
name, rad = sys.argv[1], float(sys.argv[2]); here = os.path.dirname(os.path.abspath(__file__))
s = json.load(open(os.path.join(here, 'spec', name + '.json'))); lat, lon = s['lat'], s['lon']
q = f'[out:json][timeout:300];(relation["leisure"](around:{rad},{lat},{lon});relation["landuse"](around:{rad},{lat},{lon});relation["natural"](around:{rad},{lat},{lon}););out geom tags;'
d = json.loads(urllib.request.urlopen(urllib.request.Request('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode(), headers={'User-Agent': 'stadium-scene-prototype/0.1'}), timeout=300).read())
p = os.path.join(here, 'data', name, 'osm.json'); shutil.copy(p, p + '.bak_rel'); o = json.load(open(p, encoding='utf-8'))
have = {(e['type'], e['id']) for e in o['elements']}; new = [e for e in d['elements'] if (e['type'], e['id']) not in have]
o['elements'] += new; json.dump(o, open(p, 'w', encoding='utf-8'))
for e in new: print(e['id'], {k: v for k, v in e.get('tags', {}).items() if k in ('leisure', 'landuse', 'natural', 'name')})
