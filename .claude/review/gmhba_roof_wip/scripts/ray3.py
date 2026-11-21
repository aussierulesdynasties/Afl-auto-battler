import bpy,sys,math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene
for ai in (140.5,150.5,160.5):
  for r in range(84,140,4):
    a=math.radians(ai);o=Vector((r*math.cos(a),r*math.sin(a),80));out=[]
    for k in range(4):
      hit,loc,n,idx,ob,_=sc.ray_cast(dg,o,Vector((0,0,-1)))
      if not hit:break
      out.append('%s:%.1f'%(ob.material_slots[ob.data.polygons[idx].material_index].material.name[:9],loc.z));o=loc-Vector((0,0,0.01))
    print('H',ai,r,' '.join(out))
