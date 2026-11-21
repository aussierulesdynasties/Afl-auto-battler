import bpy,sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
for o in bpy.data.objects:
  if o.type!='MESH':continue
  bb=[o.matrix_world@Vector(c) for c in o.bound_box];xs=[v.x for v in bb];ys=[v.y for v in bb];zs=[v.z for v in bb]
  if max(xs)>-140 and min(xs)<-95 and max(ys)>-65 and min(ys)<40:
    print('OBJ',o.name,[m.name for m in o.data.materials][:4],'x %.1f %.1f y %.1f %.1f z %.1f %.1f'%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
