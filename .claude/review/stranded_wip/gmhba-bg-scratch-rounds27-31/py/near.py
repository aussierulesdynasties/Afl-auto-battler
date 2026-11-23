import json,math,sys
sp=json.load(open('proto/spec/gmhba.json')); lat0,lon0=sp['lat'],sp['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('proto/data/gmhba/osm.json',encoding='utf-8'))['elements']
for tx,ty in [(183.1,166.8),(183.1,-166.8),(252,121.7)]:
  for e in js:
    for g in e.get('geometry',[]) or []:
      if not g: continue
      x=(g['lon']-lon0)*KX; y=(g['lat']-lat0)*KY
      if abs(x-tx)<40 and abs(y-ty)<8:
        print(tx,ty,e['id'],{k:v for k,v in e.get('tags',{}).items() if k in('highway','railway','landuse','barrier','footway','surface','name','leisure')}); break
