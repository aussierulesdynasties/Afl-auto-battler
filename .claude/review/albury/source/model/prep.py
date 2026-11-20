# System-python prep: triangulate ground surfaces with shapely; write model/ground.json for build.py.
import json,shapely
from shapely.geometry import Polygon
D=json.load(open('osm/geo.json',encoding='utf-8'))
def P(i):return Polygon(D[str(i)]['pts'])
def tris(g):
    out=[]
    for t in shapely.constrained_delaunay_triangles(g).geoms:out.append([list(c) for c in list(t.exterior.coords)[:3]])
    return out
venue=P(241186783).buffer(0);pitch=P(172505110).buffer(0)
court=P(237757503).buffer(0);inner=court.buffer(-2.2,join_style=2)
apron=venue.difference(pitch).difference(court)
G=dict(apron=tris(apron),court_red=tris(court.difference(inner)),court_green=tris(inner),
       pitch=[list(c) for c in pitch.exterior.coords])
json.dump(G,open('model/ground.json','w'));print({k:len(v) for k,v in G.items()},round(venue.area),round(pitch.area))
