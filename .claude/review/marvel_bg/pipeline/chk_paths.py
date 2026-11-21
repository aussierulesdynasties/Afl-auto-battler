"""OSM tags of footway/path ways that pass through the yard box (x 140..260, y -60..200)."""
import json, math, collections
S = json.load(open('spec/marvel.json')); lat0, lon0 = S['lat'], S['lon']
KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
els = json.load(open('data/marvel/osm.json', encoding='utf-8'))['elements']
C = collections.Counter()
for el in els:
    t = el.get('tags', {})
    if el.get('type') != 'way' or t.get('highway') not in ('footway', 'path', 'cycleway', 'pedestrian'): continue
    for p in el.get('geometry') or []:
        if not p: continue
        x, y = (p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY
        if 140 < x < 260 and -60 < y < 200:
            C[tuple(sorted((k, v) for k, v in t.items() if k not in ('name', 'source', 'surface:note')))] += 1; break
for k, v in C.most_common(): print(v, k)
