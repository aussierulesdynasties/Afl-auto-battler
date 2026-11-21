import json, math
spec=json.load(open('spec/adelaide.json')); lat0,lon0=spec['lat'],spec['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('data/adelaide/osm.json',encoding='utf-8'))['elements']
for el in js:
    t=el.get('tags',{})
    if t.get('natural')=='water' or 'waterway' in t:
        print(el['type'],el['id'],{k:t[k] for k in t if k in('natural','water','waterway','name','type')}, len(el.get('members',[])) or len(el.get('geometry',[])))
