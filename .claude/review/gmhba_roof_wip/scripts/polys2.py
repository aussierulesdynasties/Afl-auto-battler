import bpy,sys,json
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
out={}
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world
  for p in o.data.polygons:
    c=M@p.center
    if c.x>-60 or c.z<12: continue
    out.setdefault(o.name,[]).append([[(M@o.data.vertices[i].co).x,(M@o.data.vertices[i].co).y] for i in p.vertices])
json.dump(out,open(a[1],'w'))
