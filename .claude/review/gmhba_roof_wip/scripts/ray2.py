import bpy,sys,math,collections
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene;C=collections.Counter()
for ai in range(130,179):
  for r in range(80,150,2):
    a=math.radians(ai+0.5);hit,loc,n,idx,ob,_=sc.ray_cast(dg,Vector((r*math.cos(a),r*math.sin(a),80)),Vector((0,0,-1)))
    if hit:
      m=ob.material_slots[ob.data.polygons[idx].material_index].material.name;C[(ob.name,m,round(n.z,1))]+=1
print('R',C.most_common(20))
