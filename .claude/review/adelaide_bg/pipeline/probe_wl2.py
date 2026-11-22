import json, math, numpy as np
from shapely.geometry import Polygon
import shapely
spec=json.load(open('spec/adelaide.json')); lat0,lon0=spec['lat'],spec['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('data/adelaide/osm.json',encoding='utf-8'))['elements']
near=np.load('data/adelaide/prep/near_h.npy'); NEAR=1500; NS=2*NEAR/400
def h(x,y): return near[min(max(int(round((y+NEAR)/NS)),0),400), min(max(int(round((x+NEAR)/NS)),0),400)]
for el in js:
    t=el.get('tags',{})
    if t.get('natural')=='water' and el['type']=='way':
        pts=[((p['lon']-lon0)*KX,(p['lat']-lat0)*KY) for p in el['geometry'] if p]
        P=Polygon(pts).buffer(0).intersection(shapely.box(-1498,-1498,1498,1498))
        if P.is_empty: continue
        bz=[h(x,y) for x,y in shapely.segmentize(P.boundary,5).coords] if P.geom_type=='Polygon' else [0]
        print(el['id'],t.get('name'),'area',round(P.area),'bounds',[round(b) for b in P.bounds],'shore min/p10/med/max',np.round([min(bz),np.percentile(bz,10),np.median(bz),max(bz)],2))
