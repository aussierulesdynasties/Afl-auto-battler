import bpy,sys
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
o=bpy.data.objects['gmhba'];M=o.matrix_world;names=[s.material.name for s in o.material_slots];q={}
for p in o.data.polygons:
  if names[p.material_index] not in ('tower','lamp'):continue
  c=M@p.center
  k0='hi' if c.z>50 else ('lo' if c.z<3 else None)
  if not k0:continue
  k=(c.x>0,c.y>0,k0);q.setdefault(k,[]).append((c.x,c.y))
for k,v in q.items():print('TWR',k,'%.2f %.2f n%d'%(sum(a for a,b in v)/len(v),sum(b for a,b in v)/len(v),len(v)))
