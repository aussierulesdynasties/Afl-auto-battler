import bpy,sys,math,collections
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
B={};C=collections.Counter()
for o in bpy.data.objects:
  if o.type!='MESH':continue
  M=o.matrix_world
  for p in o.data.polygons:
    c=M@p.center
    if c.x<-95 and -40<c.y<60:
      n=o.data.materials[p.material_index].name if o.data.materials else '-'
      C[n]+=1;b=B.setdefault(n,[1e9,-1e9,1e9,-1e9,1e9,-1e9])
      for i,v in enumerate((c.x,c.y,c.z)):b[2*i]=min(b[2*i],v);b[2*i+1]=max(b[2*i+1],v)
for n,k in C.most_common():print(n,k,[round(v,1) for v in B[n]])
