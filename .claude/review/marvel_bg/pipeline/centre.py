import json,sys,math
for n in sys.argv[1:]:
    js=json.load(open(f'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/data/{n}/osm.json',encoding='utf-8'))['elements']
    for e in js:
        t=e.get('tags',{})
        if t.get('leisure') in ('pitch','stadium','sports_centre') and ('australian_football' in t.get('sport','') or 'cricket' in t.get('sport','') or t.get('leisure')=='stadium'):
            g=[p for p in e.get('geometry',[]) if p]
            if not g: continue
            la=sum(p['lat'] for p in g)/len(g); lo=sum(p['lon'] for p in g)/len(g)
            print(n,e['id'],t.get('leisure'),t.get('sport'),t.get('name'),round(la,6),round(lo,6),len(g))
