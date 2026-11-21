import sys, json, numpy as np
src=open('meas_table.py',encoding='utf-8').read()
cut=src.index("spec = json.load"); cut2=src.index("rows.append(('Water area")
exec(src[:cut]); exec(src[cut:cut2])
from scipy import ndimage
from skimage import measure
from shapely.geometry import Polygon
D=W1&~ndimage.binary_dilation(W2,iterations=2)
# SW golf box in world coords -> px
x0,x1,y0,y1=-620,-250,-720,-540
px0,px1,py0,py1=x0+700,x1+700,700-y1,700-y0
box=np.zeros_like(D); box[py0:py1,px0:px1]=1
D=ndimage.binary_opening(D&box.astype(bool),iterations=1)
lab,n=ndimage.label(D); sz=ndimage.sum(D,lab,range(1,n+1))
base=json.load(open('spec/peoplefirst_pre10c.json'))
added=[]
for k in range(n):
    if sz[k]<120: continue
    m=(lab==k+1)
    for c in measure.find_contours(np.pad(m,1).astype(float),0.5):
        if len(c)<8: continue
        pts=[(float(x-1-700),float(700-(y-1))) for y,x in c]
        g=Polygon(pts).simplify(1.0)
        if not g.is_valid: g=g.buffer(0)
        if g.area<120: continue
        if g.geom_type=='MultiPolygon': g=max(g.geoms,key=lambda q:q.area)
        added.append(['water',[[round(a,1),round(b,1)] for a,b in g.exterior.coords]])
        print('added',int(g.area),'m2 at',[round(v) for v in g.centroid.coords[0]])
base['paint_poly']+=added
json.dump(base,open('spec/peoplefirst_pre10c.json','w'),indent=1)
print(len(added),'polys')
