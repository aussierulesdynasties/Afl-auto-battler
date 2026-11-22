import json, math
S=json.load(open('spec/marvel.json')); lat0,lon0=S['lat'],S['lon']; KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('data/marvel/osm.json',encoding='utf-8'))['elements']
N={e['id']:e for e in js if e['type']=='node'}
for nm in ['Wurundjeri Way','Footscray Road','Bolte Bridge','Docklands']:
    xs=[];ys=[]
    for e in js:
        if e.get('tags',{}).get('name')==nm:
            if e['type']=='way':
                for i in e.get('nodes',[]):
                    if i in N: xs.append((N[i]['lon']-lon0)*KX); ys.append((N[i]['lat']-lat0)*KY)
                for g in e.get('geometry',[]): xs.append((g['lon']-lon0)*KX); ys.append((g['lat']-lat0)*KY)
            else: print(nm, e['type'], e.get('tags',{}).get('boundary'))
    if xs: print(nm, 'x', round(min(xs)), round(max(xs)), 'y', round(min(ys)), round(max(ys)))
