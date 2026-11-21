import bpy,sys
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
S=set()
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world
  for v in o.data.vertices:
    c=M@v.co
    if -60<c.y<90 and c.x<-75 and c.x>-100 and c.z>20 and c.z<40 and c.y>-50 and o.name=="gmhba" and c.y<5: S.add((round(c.x,1),round(c.y,1),round(c.z,1),o.name))
for s in sorted(S,key=lambda s:-s[1]):
  if s[2]>=20: print('V',s)
