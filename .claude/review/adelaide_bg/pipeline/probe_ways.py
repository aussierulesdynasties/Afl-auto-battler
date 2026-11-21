import json, math, sys
spec = json.load(open('spec/traeger.json')); lat0, lon0 = spec['lat'], spec['lon']
KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
js = json.load(open('data/traeger/osm.json', encoding='utf-8'))['elements']
for el in js:
    if el['type'] != 'way' or 'geometry' not in el: continue
    t = el.get('tags', {})
    if not any(k in t for k in ('leisure', 'sport', 'landuse')): continue
    pts = [((p['lon'] - lon0) * KX, (p['lat'] - lat0) * KY) for p in el['geometry'] if p]
    if len(pts) < 4 or pts[0] != pts[-1]: continue
    cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)
    if -120 < cx < 170 and 30 < cy < 230:
        print(round(cx), round(cy), {k: t[k] for k in ('leisure', 'sport', 'landuse', 'surface') if k in t})
