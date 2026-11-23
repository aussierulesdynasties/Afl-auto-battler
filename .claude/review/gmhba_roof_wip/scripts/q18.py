import bpy,sys
f=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=f)
for want in ('beige','wedge','wedgef'):
  xs=[];ys=[];zs=[]
  for o in bpy.data.objects:
    if o.type!='MESH':continue
    M=o.matrix_world;me=o.data
    for p in me.polygons:
      if not me.materials or me.materials[p.material_index].name!=want:continue
      c=M@p.center
      if not(c.x<-108 and -45<c.y<34):continue
      for vi in p.vertices:
        v=M@me.vertices[vi].co;xs.append(v.x);ys.append(v.y);zs.append(v.z)
  print(want,[round(min(xs),1),round(max(xs),1),round(min(ys),1),round(max(ys),1),round(min(zs),1),round(max(zs),1)])
