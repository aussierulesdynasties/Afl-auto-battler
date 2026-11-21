import bpy,sys
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
rows=[17,-3.5,-11.5,-17,-22,-31]
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;me=o.data;names=[s.material.name if s.material else '?' for s in o.material_slots]
  res={}
  for p in me.polygons:
    c=M@p.center
    # glTF import: Blender x=east?, y=north? report raw
    for r in rows:
      if abs(c.y-r)<0.8 and -100<c.x<-30 and c.z<3:
        k=(r,names[p.material_index]);res[k]=(max(res.get(k,(-1e9,0))[0],c.x),c.z)
  for k in sorted(res):print('ROW',o.name,k,'%.2f z%.1f'%res[k])
