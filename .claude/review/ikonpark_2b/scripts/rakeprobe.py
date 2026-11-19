import bpy,sys
from mathutils import Vector
glb=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene
for y in range(96,132,2):
    hit,loc,n,idx,ob,_=sc.ray_cast(dg,Vector((47.58,y,80)),Vector((0,0,-1)))
    mat=ob.material_slots[ob.data.polygons[idx].material_index].material.name if hit else ''
    print('Z',y,hit and round(loc.z,2),mat)
