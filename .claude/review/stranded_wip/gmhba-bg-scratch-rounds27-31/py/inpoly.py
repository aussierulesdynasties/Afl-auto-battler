import json,math
from matplotlib.path import Path
sp=json.load(open('proto/spec/gmhba.json')); lat0,lon0=sp['lat'],sp['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('proto/data/gmhba/osm.json',encoding='utf-8'))['elements']
for t in [(77.3,109.9),(92.7,81.6)]:
  for e in js:
    g=e.get('geometry')
    if e['type']!='way' or not g or len(g)<4: continue
    pts=[((p['lon']-lon0)*KX,(p['lat']-lat0)*KY) for p in g]
    if Path(pts).contains_point(t) and 'building' in e.get('tags',{}): print(t,e['id'],e.get('tags'),round(min(math.hypot(*p) for p in pts)))
