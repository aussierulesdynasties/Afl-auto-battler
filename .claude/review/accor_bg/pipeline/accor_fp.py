import json,math
lat0,lon0=-33.84722,151.06333;KX=111320*math.cos(math.radians(lat0));KY=110540
E=json.load(open('data/accor/osm.json',encoding='utf-8'))['elements']
for e in E:
    t=e.get('tags',{})
    if e['type']=='way' and 'geometry' in e and (t.get('leisure')=='stadium' or t.get('building')=='stadium' or 'Accor' in t.get('name','') or 'Stadium Australia' in t.get('name','')):
        P=[((g['lon']-lon0)*KX,(g['lat']-lat0)*KY) for g in e['geometry']]
        cx=sum(p[0] for p in P)/len(P);cy=sum(p[1] for p in P)/len(P)
        print(e['id'],t.get('name'),t.get('leisure'),t.get('building'),len(P),round(cx),round(cy),round(max(math.hypot(x-cx,y-cy) for x,y in P)))
