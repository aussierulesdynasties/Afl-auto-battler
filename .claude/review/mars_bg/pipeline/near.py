import json,math,numpy as np
sp=json.load(open('spec/peoplefirst.json')); lat0,lon0=sp['lat'],sp['lon'];KX=111320*math.cos(math.radians(lat0));KY=110540
for e in json.load(open('data/peoplefirst/osm.json',encoding='utf-8'))['elements']:
    g=[q for q in (e.get('geometry') or []) if q]
    if len(g)<2: continue
    P=np.array([((q['lon']-lon0)*KX,(q['lat']-lat0)*KY) for q in g])
    for tx,ty in [(-94,-342.2),(-93.3,-342)]:
        d=min(np.hypot(*(P-[tx,ty]).T))
        # segment distance approx via densify
        Q=np.concatenate([np.linspace(a,b,20) for a,b in zip(P,P[1:])]); d=np.hypot(*(Q-[tx,ty]).T).min()
        if d<10: print(e['id'],e.get('tags'),round(d,1)); break
