import bpy,sys,json
a=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
out={}
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;names=[s.material.name if s.material else '' for s in o.material_slots]
  for p in o.data.polygons:
    n=names[p.material_index]
    if n not in ('jss_canopy','jss_block','jss_white','jss_clad','jss_top','tower'):continue
    out.setdefault(n,[]).append([[(M@o.data.vertices[i].co).x,(M@o.data.vertices[i].co).y] for i in p.vertices])
json.dump(out,open(a[1],'w'))
