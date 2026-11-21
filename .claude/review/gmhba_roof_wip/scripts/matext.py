import bpy,sys
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;names=[s.material.name if s.material else '?' for s in o.material_slots];ext={}
  for v in o.data.polygons:
    c=M@v.center;n=names[v.material_index];e=ext.setdefault(n,[1e9,-1e9,1e9,-1e9,1e9,-1e9])
    e[0]=min(e[0],c.x);e[1]=max(e[1],c.x);e[2]=min(e[2],c.y);e[3]=max(e[3],c.y);e[4]=min(e[4],c.z);e[5]=max(e[5],c.z)
  for n,e in sorted(ext.items()):print('EXT',o.name,n,' '.join('%.1f'%x for x in e))
