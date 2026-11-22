"""Refetch natural=water relations WITH member geometry and replace them in osm.json. fetch_rel.py name lat lon"""
import sys,json,time,urllib.request,urllib.parse
n,la,lo=sys.argv[1:4]
q=f'[out:json][timeout:180];relation["natural"="water"](around:3000,{la},{lo});out geom;'
for i in range(8):
    u=('https://overpass-api.de/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter')[i%2]
    try: d=urllib.request.urlopen(urllib.request.Request(u,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'scene-proto/0.1'}),timeout=150).read();break
    except Exception as e: print('retry',e,flush=True);time.sleep(5)
R=json.loads(d)['elements'];p=f'data/{n}/osm.json';J=json.load(open(p,encoding='utf-8'))
J['elements']=[e for e in J['elements'] if e['type']!='relation']+R
json.dump(J,open(p,'w',encoding='utf-8'))
print('relations',len(R),'members',sum(len(e.get('members',[])) for e in R))
