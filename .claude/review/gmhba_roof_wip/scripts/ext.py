import bpy,sys
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;names=[s.material.name if s.material else '' for s in o.material_slots];q={}
  for p in o.data.polygons:
    n=names[p.material_index] if names else ''
    c=M@p.center
    if c.x>-100 or c.y<0: continue
    q.setdefault((o.name,n),[]).append(c)
  for k,v in q.items(): print('EXT',k,len(v),'x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f'%(min(c.x for c in v),max(c.x for c in v),min(c.y for c in v),max(c.y for c in v),min(c.z for c in v),max(c.z for c in v)))
