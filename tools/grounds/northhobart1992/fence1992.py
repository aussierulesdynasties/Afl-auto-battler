# Fence as seen on the Land Tasmania aerial 1182_185 (16 Feb 1992): offsets (m, + out) read every 5 deg off the rectified aerial
# (fence_offsets_1992.json) applied along the old fence's normal; old world kept in world_pre1992fence.json.
# new fence = old fence point at each bearing (5 deg, from C0) moved along the old fence normal by the offset read off the 1992 aerial
import json,math,numpy as np
from shapely.geometry import Polygon,LineString
NH=''
OFS=json.load(open('fence_offsets_1992.json'))
import os
if os.path.exists('world_pre1992fence.json'):D0=json.load(open('world_pre1992fence.json'))
else:D0=json.load(open(NH+'world.json'));json.dump(D0,open('world_pre1992fence.json','w'),indent=0)
D=D0;ex=Polygon(D['fences'][0]['xy']).exterior;C0=np.array([-5.0,-1.6])
bs=sorted(int(k) for k in OFS);out=[]
for brg in np.arange(0,360,2.5):
    # interpolate offset between 5-degree reads
    a=int(brg//5*5)%360;b=(a+5)%360;f=(brg-brg//5*5)/5;o=OFS[str(a)]*(1-f)+OFS[str(b)]*f
    t=math.radians(brg);d=np.array([math.sin(t),math.cos(t)])
    ip=LineString([C0,C0+d*200]).intersection(ex);ip=ip if ip.geom_type=='Point' else list(ip.geoms)[0]
    s=ex.project(ip);pa=np.array(ex.interpolate(s-1).coords[0]);pb=np.array(ex.interpolate(s+1).coords[0])
    tg=(pb-pa)/np.linalg.norm(pb-pa);n=np.array([tg[1],-tg[0]]);q=np.array(ip.coords[0])
    if np.dot(n,q-C0)<0:n=-n
    out.append([float(v) for v in q+n*o])
P=Polygon(out);print('valid',P.is_valid,'area old',round(Polygon(D['fences'][0]['xy']).area),'new',round(P.area))
W=json.load(open('world.json'));W['fences'][0]['xy']=out;json.dump(W,open('world.json','w',newline=''),indent=0)
