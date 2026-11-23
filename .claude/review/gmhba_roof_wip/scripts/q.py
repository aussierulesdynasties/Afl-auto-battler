import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
for o in bpy.data.objects:
  if o.type!='MESH' or o.name=='jss_roof':continue
  M=o.matrix_world;names=[s.material.name for s in o.material_slots];C=collections.Counter();Z={}
  for p in o.data.polygons:
    c=M@p.center;a=math.degrees(math.atan2(c.y,c.x));a=a+360 if a<0 else a;r=math.hypot(c.x,c.y)
    if 126<a<182 and r>86 and c.z>3:
      n=(M.to_3x3()@p.normal).normalized();k=(names[p.material_index],'flat' if abs(n.z)>0.9 else 'vert' if abs(n.z)<0.1 else 'slant')
      C[k]+=1;z=Z.setdefault(k,[1e9,-1e9,1e9,-1e9,1e9,-1e9]);z[0]=min(z[0],c.z);z[1]=max(z[1],c.z);z[2]=min(z[2],r);z[3]=max(z[3],r);z[4]=min(z[4],a);z[5]=max(z[5],a)
  for k,v in sorted(C.items()):print('Q',k,v,['%.0f'%x for x in Z[k]])
