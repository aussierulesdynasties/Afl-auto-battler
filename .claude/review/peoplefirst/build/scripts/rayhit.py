# usage: blender -b model.blend -P rayhit.py -- x,y x,y ...   (photo pixel -> first hit object/material/point, cam.json projection)
import bpy,json,sys,math
import numpy as np
from mathutils import Vector
p=json.load(open('cam.json'))['p'];Wi,Hi=2000,1333
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
Rm=R(*p[3:6]);dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene
for s in sys.argv[sys.argv.index('--')+1:]:
    x,y=map(float,s.split(','));d=np.array([(x-Wi/2)/p[6],-(y-Hi/2)/p[6],1.0])@Rm;d/=np.linalg.norm(d)
    ok,loc,n,fi,ob,_=sc.ray_cast(dg,Vector(p[:3]),Vector(d))
    if ok:
        m=ob.data.materials[ob.data.polygons[fi].material_index].name if ob.type=='MESH' and ob.data.materials else '-'
        print(f'HIT {s}: {ob.name} mat {m} at ({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) r {math.hypot(loc.x,loc.y):.1f} ang {math.degrees(math.atan2(loc.y,loc.x))%360:.1f}')
    else:print('HIT',s,'none')
