import json, math, sys
from matplotlib.path import Path
s = json.load(open('spec/adelaide.json')); lat0, lon0 = s['lat'], s['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
xy = lambda a, b: ((b - lon0) * KX, (a - lat0) * KY)
js = json.load(open('data/adelaide/osm.json', encoding='utf-8'))['elements']
for X, Y in [(-350, 150), (-700, 300), (300, 650), (-300, -50)]:
    hits = []
    for e in js:
        t = e.get('tags', {})
        if not any(k in t for k in ('leisure', 'landuse', 'natural', 'golf')): continue
        rings = [e['geometry']] if e['type'] == 'way' and 'geometry' in e else [m['geometry'] for m in e.get('members', []) if m.get('role') == 'outer' and m.get('geometry')]
        for r in rings:
            p = [xy(q['lat'], q['lon']) for q in r if q]
            if len(p) > 2 and Path(p).contains_point((X, Y)): hits.append((e['type'], e['id'], {k: t[k] for k in t if k in ('leisure', 'landuse', 'natural', 'golf', 'name')}, p[0] == p[-1]))
    print((X, Y), hits)
