"""OSM fetch split into one request per clause (big combined query 502s). fetch_split.py name lat lon rad"""
import sys,os,json,time,urllib.request,urllib.parse
n,la,lo,rad=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4])
C=[f'way["building"](around:{rad},{la},{lo})',f'way["landuse"](around:1500,{la},{lo})',f'way["leisure"](around:1500,{la},{lo})',
 f'way["natural"](around:3000,{la},{lo})',f'relation["natural"="water"](around:3000,{la},{lo})',f'way["waterway"](around:3000,{la},{lo})',
 f'way["highway"](around:1500,{la},{lo})',f'way["railway"](around:1500,{la},{lo})',f'node["natural"="tree"](around:800,{la},{lo})']
EL=[];seen=set()
for c in C:
    for i in range(6):
        for u in ('https://overpass-api.de/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter','https://overpass.private.coffee/api/interpreter'):
            try:
                d=urllib.request.urlopen(urllib.request.Request(u,data=urllib.parse.urlencode({'data':f'[out:json][timeout:180];{c};out geom tags;'}).encode(),headers={'User-Agent':'scene-proto/0.1'}),timeout=90).read();break
            except Exception as e: print('retry',c[:20],u[8:20],e); d=None; time.sleep(4)
        if d: break
    if not d: sys.exit('fail '+c)
    for e in json.loads(d)['elements']:
        k=(e['type'],e['id'])
        if k not in seen: seen.add(k);EL.append(e)
    print(c[:30],len(EL),flush=True)
json.dump({'elements':EL},open(f'data/{n}/osm.json','w',encoding='utf-8'))
