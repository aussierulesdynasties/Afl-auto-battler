import bpy,sys
from mathutils import Vector
glb,x,y,z=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=glb)
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene;o=Vector((float(x),float(y),float(z)))
for d in [(0,0,1),(0,0,-1),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,-1,0.3),(0.5,-1,0.3)]:
    hit,loc,nrm,idx,ob,_=sc.ray_cast(dg,o,Vector(d).normalized())
    mat=ob.material_slots[ob.data.polygons[idx].material_index].material.name if hit and ob.material_slots else ''
    print('RAY',d,hit and ob.name,hit and tuple(round(c,2) for c in loc),mat)
