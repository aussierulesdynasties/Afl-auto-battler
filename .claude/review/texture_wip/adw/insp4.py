import bpy,sys,math,collections
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"adelaide_es2.glb")
for o in bpy.data.objects:
  if o.type!='MESH':continue
  me=o.data;mw=o.matrix_world;h=collections.defaultdict(lambda:[0,1e9,-1e9,1e9,-1e9])
  for p in me.polygons:
    n=mw.to_3x3()@p.normal
    if abs(n.z)>0.3: continue
    c=mw@p.center
    if n.x*c.x+n.y*c.y<=0: continue
    az=math.degrees(math.atan2(c.y,c.x)); r=math.hypot(c.x,c.y)
    k=(o.name,me.materials[p.material_index].name,int(az//10)*10); e=h[k]; e[0]+=p.area; e[1]=min(e[1],c.z);e[2]=max(e[2],c.z);e[3]=min(e[3],r);e[4]=max(e[4],r)
  for k,e in sorted(h.items(),key=lambda x:x[0][2]):
    if e[0]>30 and k[1] in ("stands","hotel"): print(k,[round(x) for x in e])
print("CAM",[(round(math.degrees(math.atan2(c.location.y,c.location.x))),) for c in bpy.data.objects if c.type=='CAMERA'])
