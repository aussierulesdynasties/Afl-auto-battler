import json, math
spec=json.load(open('spec/adelaide.json')); lat0,lon0=spec['lat'],spec['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('data/adelaide/osm.json',encoding='utf-8'))['elements']
def xy(p): return ((p['lon']-lon0)*KX,(p['lat']-lat0)*KY)
from collections import Counter
c=Counter()
for el in js:
    t=el.get('tags',{}); g=el.get('geometry')
    if not g: continue
    pts=[xy(p) for p in g if p]
    if not pts: continue
    d=min(math.hypot(*q) for q in pts)
    if t.get('sport')=='tennis' and d<400: print('tennis',el['type'],el['id'],t, [tuple(round(v,1) for v in q) for q in pts])
    if d<400 and (t.get('highway') or t.get('area:highway') or t.get('place')=='square'): c[(el['type'],t.get('highway'),t.get('area'),t.get('area:highway'),t.get('place'))]+=1
    if el.get('id')==1116828761: print('oval2',t)
for k,v in c.items(): print(k,v)
