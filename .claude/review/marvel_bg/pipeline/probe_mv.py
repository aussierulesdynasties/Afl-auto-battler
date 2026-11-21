import json,math,numpy as np
s=json.load(open('spec/marvel.json'));lat0,lon0=s['lat'],s['lon'];KX=111320*math.cos(math.radians(lat0));KY=110540
FP=np.array(json.load(open('data/marvel/prep/footprint.json')))
for e in json.load(open('data/marvel/osm.json',encoding='utf-8'))['elements']:
    t=e.get('tags',{})
    if 'building' not in t or not e.get('geometry'):continue
    P=[((q['lon']-lon0)*KX,(q['lat']-lat0)*KY) for q in e['geometry'] if q]
    ins=[math.hypot(x,y)<FP[int(math.degrees(math.atan2(y,x))%360//2)]+2 for x,y in P]
    if any(ins):print(e['id'],t.get('name'),t.get('building'),t.get('height'),t.get('building:levels'),sum(ins),len(P),round(math.hypot(*np.mean(P,0))))
