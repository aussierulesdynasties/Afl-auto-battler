import json, math, numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import shapely
spec=json.load(open('spec/adelaide.json')); lat0,lon0=spec['lat'],spec['lon']
KX=111320*math.cos(math.radians(lat0)); KY=110540
js=json.load(open('data/adelaide/osm.json',encoding='utf-8'))['elements']
near=np.load('data/adelaide/prep/near_h.npy'); NEAR=1500; NS=2*NEAR/400
def h(x,y): return near[min(max(int(round((y+NEAR)/NS)),0),400), min(max(int(round((x+NEAR)/NS)),0),400)]
PS={}
for el in js:
    t=el.get('tags',{})
    if t.get('natural')=='water' and el['type']=='way':
        pts=[((p['lon']-lon0)*KX,(p['lat']-lat0)*KY) for p in el['geometry'] if p]
        P=Polygon(pts).buffer(0).intersection(shapely.box(-1498,-1498,1498,1498))
        if not P.is_empty and P.area>100: PS[el['id']]=P
for k,P in PS.items():
    oth=unary_union([q for j,q in PS.items() if j!=k]).buffer(3)
    pts=[(x,y) for x,y in shapely.segmentize(P.boundary,5).coords if not oth.contains(Point(x,y))] if P.geom_type=='Polygon' else []
    bz=[h(x,y) for x,y in pts]
    if bz:
        a=np.argmin(bz); print(k,'min',round(min(bz),2),'at',np.round(pts[a]),'p10',round(np.percentile(bz,10),2),'med',round(np.median(bz),2))
