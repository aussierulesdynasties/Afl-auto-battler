import bpy,sys,collections
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
G=collections.defaultdict(list)
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world;me=o.data
  for v in me.vertices:
    w=M@v.co
    if w.z>45:G[(round(w.x/20),round(w.y/20))].append(w)
for k,vs in G.items():
  import statistics as s
  print(k,len(vs),'x',round(s.mean(v.x for v in vs),1),'y',round(s.mean(v.y for v in vs),1),'zmax',round(max(v.z for v in vs),1))
