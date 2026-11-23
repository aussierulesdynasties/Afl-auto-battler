import json, math, sys
sp = json.load(open('spec/gmhba.json')); lat0, lon0 = sp['lat'], sp['lon']; KX = 111320 * math.cos(math.radians(lat0))
for el in json.load(open('data/gmhba/osm.json', encoding='utf-8'))['elements']:
    t = el.get('tags', {})
    if el['type'] == 'way' and (t.get('leisure') in ('swimming_pool', 'sports_centre') or t.get('sport') in ('swimming', 'tennis')) and el.get('geometry'):
        p = [((g['lon'] - lon0) * KX, (g['lat'] - lat0) * 110540) for g in el['geometry']]
        cx = sum(a for a, b in p) / len(p); cy = sum(b for a, b in p) / len(p)
        if math.hypot(cx, cy) < 700: print(el['id'], {k: v for k, v in t.items() if k in ('leisure', 'sport', 'name', 'access', 'location')}, round(cx), round(cy), len(p))
