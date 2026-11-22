import json, math, numpy as np
lat0, lon0 = -33.847086, 151.063400; KX = 111320*math.cos(math.radians(lat0)); KY = 110540
E_ = json.load(open('data/accor/osm.json', encoding='utf-8'))['elements']
for e in E_:
    t = e.get('tags', {}); n = (t.get('name','') + ' ' + t.get('building','')).lower()
    if e['type']=='way' and 'geometry' in e and any(k in n for k in ('qudos','arena','dome','pavilion','hall','station','superdome')):
        P = np.array([((g['lon']-lon0)*KX, (g['lat']-lat0)*KY) for g in e['geometry']])
        print(e['id'], t.get('name'), t.get('building'), t.get('height'), t.get('building:levels'), P.mean(0).round(0), (P.max(0)-P.min(0)).round(0))
