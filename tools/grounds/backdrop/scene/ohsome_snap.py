"""OSM as it was on a date (ohsome API, HeiGIT; data (c) OpenStreetMap contributors, ODbL), written in the
pipeline's osm.json shape (ways with geometry, multipolygon relations with member geometry, tagged nodes).
usage: ohsome_snap.py current_osm.json out.json YYYY-MM-DD"""
import sys, json, urllib.request, urllib.parse
src, out, date = sys.argv[1:4]
E = json.load(open(src))['elements']
la = [p['lat'] for x in E if x['type'] == 'way' for p in x.get('geometry', []) if p]
lo = [p['lon'] for x in E if x['type'] == 'way' for p in x.get('geometry', []) if p]
bb = '%.6f,%.6f,%.6f,%.6f' % (min(lo), min(la), max(lo), max(la))
KEYS = ('building', 'highway', 'natural', 'amenity', 'leisure', 'landuse', 'railway', 'man_made', 'waterway', 'water', 'tourism', 'barrier', 'place', 'surface')
flt = '(' + ' or '.join('%s=*' % k for k in KEYS) + ')'
def get(f):
    import datetime as _dt; d2 = (_dt.date.fromisoformat(date) + _dt.timedelta(days=1)).isoformat()
    q = urllib.parse.urlencode(dict(bboxes=bb, time=date + ',' + d2, filter=f, properties='tags'))   # the version valid that day (the plain snapshot route is refused here)
    r = urllib.request.urlopen(urllib.request.Request('https://api.ohsome.org/v1/elementsFullHistory/geometry?' + q, headers={'User-Agent': 'scene-builder/0.1'}), timeout=900)
    return json.load(r)['features']
els = []
def geo(cs): return [{'lat': c[1], 'lon': c[0]} for c in cs]
for typ in ('way', 'relation', 'node'):
    F = get(flt + ' and type:' + typ)
    seen = set()
    for f in F:
        p = f['properties']
        if p.get('@validFrom', '') > date + 'T00:00:00Z' or p['@osmId'] in seen: continue
        seen.add(p['@osmId']); oid = int(p['@osmId'].split('/')[1]); tags = {k: v for k, v in p.items() if not k.startswith('@')}
        g = f['geometry']
        if typ == 'node':
            if g['type'] == 'Point': els.append(dict(type='node', id=oid, lat=g['coordinates'][1], lon=g['coordinates'][0], tags=tags))
        elif typ == 'way':
            cs = g['coordinates'][0] if g['type'] == 'Polygon' else g['coordinates'] if g['type'] == 'LineString' else None
            if cs: els.append(dict(type='way', id=oid, geometry=geo(cs), tags=tags))
        else:
            polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates'] if g['type'] == 'MultiPolygon' else []
            mem = [dict(type='way', ref=0, role='outer' if i == 0 else 'inner', geometry=geo(r)) for P in polys for i, r in enumerate(P)]
            if mem: els.append(dict(type='relation', id=oid, tags=dict(tags, type=tags.get('type', 'multipolygon')), members=mem))
    print(typ, len(F))
json.dump({'elements': els, 'snapshot': date}, open(out, 'w'))
print('elements', len(els))
