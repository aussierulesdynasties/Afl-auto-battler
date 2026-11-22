# blender -b optus.blend --python r2/roofr.py -- OUT.json : per angle (deg, every 2), outermost radius from oc where a leaned
# vertical ray (satellite lean LEAN per metre of height) hits roof, and where it hits anything
import bpy,sys,math,json,os
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1];here=os.path.dirname(os.path.dirname(os.path.abspath(out)))
oc=json.load(open(os.path.join(here,'geom.json')))['oc'];vx,vy=[float(v) for v in os.environ.get('LEAN','-0.0365,-0.30').split(',')]
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene;R={}
for a in range(0,360,2):
  c,s=math.cos(math.radians(a)),math.sin(math.radians(a));roof=anyr=None
  r=260.0
  while r>60:
    X,Y=oc[0]+c*r,oc[1]+s*r
    hit,loc,nor,idx,ob,_=sc.ray_cast(dg,Vector((X-100*vx,Y-100*vy,100)),Vector((vx,vy,-1)).normalized())
    if hit:
      m=ob.material_slots[ob.data.polygons[idx].material_index].material.name
      if anyr is None:anyr=r
      if loc.z>40 and m.split('.')[0] in ('roof','white') and roof is None:roof=r;break
    r-=0.25
  R[a]=[roof,anyr]
json.dump(R,open(out,'w'))
