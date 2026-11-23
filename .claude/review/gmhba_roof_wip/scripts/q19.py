import bpy,sys,collections
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;me=o.data
  for p in me.polygons:
    c=M@p.center
    if -122<c.x<-118 and -46<c.y<-2 and abs(p.normal.x)>0.5:
      vs=[M@me.vertices[i].co for i in p.vertices]
      print(me.materials[p.material_index].name,[ (round(v.y,1),round(v.z,1)) for v in vs])
