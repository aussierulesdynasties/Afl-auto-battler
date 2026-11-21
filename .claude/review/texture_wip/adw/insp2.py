import bpy,sys,math,collections
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"adelaide_westback.glb")
for o in bpy.data.objects:
  if o.type!='MESH':continue
  me=o.data;mw=o.matrix_world;h=collections.defaultdict(lambda:[0,1e9,-1e9,1e9,-1e9])
  for p in me.polygons:
    if abs(p.normal.z)>0.2: continue
    c=mw@p.center; n=mw.to_3x3()@p.normal
    if n.x*c.x+n.y*c.y<=0: continue
    r=math.hypot(c.x,c.y)
    if r<80: continue
    az=math.degrees(math.atan2(c.y,c.x)); m=me.materials[p.material_index].name if me.materials else '-'
    k=(o.name,m,int(az//30)*30); e=h[k]; e[0]+=p.area; e[1]=min(e[1],c.z);e[2]=max(e[2],c.z);e[3]=min(e[3],r);e[4]=max(e[4],r)
  for k,e in sorted(h.items()):
    if e[0]>50: print(k,[round(x) for x in e])
for m in bpy.data.materials:
  ims=[n.image.name for n in (m.node_tree.nodes if m.node_tree else []) if n.type=='TEX_IMAGE' and n.image]
  bc=m.node_tree.nodes.get('Principled BSDF') if m.node_tree else None
  print("MAT",m.name,ims,[round(x,2) for x in bc.inputs['Base Color'].default_value] if bc else '')
