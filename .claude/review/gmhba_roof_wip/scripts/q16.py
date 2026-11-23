import bpy,sys,math,collections
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in a:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
  C=collections.Counter();B={}
  for o in bpy.data.objects:
    if o.type!='MESH':continue
    M=o.matrix_world
    for p in o.data.polygons:
      c=M@p.center;an=math.degrees(math.atan2(c.y,c.x))%360
      if c.x<-108 and -6<c.y<34:
        n=o.data.materials[p.material_index].name if o.data.materials else '-'
        C[n]+=1;b=B.setdefault(n,[1e9,-1e9,1e9,-1e9,1e9,-1e9])
        for i,v in enumerate((c.x,c.y,c.z)):b[2*i]=min(b[2*i],v);b[2*i+1]=max(b[2*i+1],v)
  print('==',f)
  for n,k in C.most_common():print(n,k,[round(v) for v in B[n]])
