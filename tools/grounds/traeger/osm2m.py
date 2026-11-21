import json,math
d=json.load(open('osm/traeger.json',encoding='utf-8'))
P=[e for e in d['elements'] if e['id']==242194673][0]['geometry']
lat0=sum(g['lat'] for g in P)/len(P);lon0=sum(g['lon'] for g in P)/len(P)
k=111320.0
def m(g):return ((g['lon']-lon0)*k*math.cos(math.radians(lat0)),(g['lat']-lat0)*110574.0)
G={};info={}
for e in d['elements']:
    if 'geometry' not in e:continue
    pts=[m(g) for g in e['geometry']];cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
    if math.hypot(cx,cy)>230:continue
    G[str(e['id'])]=pts;info[str(e['id'])]=(round(cx),round(cy),e.get('tags'))
json.dump({'origin':[lat0,lon0],'geo':G,'info':info},open('osm/geo.json','w'))
for k_,v in info.items():print(k_,v,len(G[k_]))
pp=G['242194673'];xs=[p[0] for p in pp];ys=[p[1] for p in pp]
print('pitch x',min(xs),max(xs),'y',min(ys),max(ys))
