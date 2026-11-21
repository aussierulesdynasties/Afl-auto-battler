import json,math
sp=json.load(open('spec/peoplefirst.json'))
print([k for k in sp]); print({k for k,p in sp.get('paint_poly',[])})
for k,p in sp.get('paint_poly',[]):
    xs=[a for a,b in p]; ys=[b for a,b in p]; print(k, round(min(xs)),round(max(xs)),round(min(ys)),round(max(ys)))
lat0,lon0=sp['lat'],sp['lon'];KX=111320*math.cos(math.radians(lat0));KY=110540
els=json.load(open('data/peoplefirst/osm.json',encoding='utf-8'))['elements']
for e in els:
    g=e.get('geometry') or []
    if e.get('type')!='way' or len(g)<3: continue
    P=[((q['lon']-lon0)*KX,(q['lat']-lat0)*KY) for q in g if q]
    xs=[a for a,b in P]; ys=[b for a,b in P]
    if min(xs)<60 and max(xs)>-160 and min(ys)<-200 and max(ys)>-400:
        t=e.get('tags',{})
        if t.get('highway') and t.get('area')!='yes' and 'amenity' not in t: continue
        print(e['id'],{k:v for k,v in t.items() if k in('amenity','landuse','highway','area','leisure','parking','building','surface','man_made','place')},round(min(xs)),round(max(xs)),round(min(ys)),round(max(ys)))
