import urllib.request, urllib.parse, json
q='[out:json];way["leisure"~"pitch|stadium"](around:400,-38.158,144.3546);out geom tags;'
d=json.loads(urllib.request.urlopen(urllib.request.Request('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'scene/0.1'}),timeout=120).read())
for e in d['elements']:
    g=e['geometry'];la=sum(p['lat'] for p in g[:-1])/(len(g)-1);lo=sum(p['lon'] for p in g[:-1])/(len(g)-1)
    print(e['id'],e['tags'].get('leisure'),e['tags'].get('sport'),e['tags'].get('name'),round(la,6),round(lo,6),len(g))
