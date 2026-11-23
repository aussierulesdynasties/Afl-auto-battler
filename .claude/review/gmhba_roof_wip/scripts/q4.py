import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
B=collections.defaultdict(lambda:[999,0])
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world
  for p in me.polygons:
    mn=ob.material_slots[p.material_index].material.name
    if not mn.startswith('roof'):continue
    for vi in p.vertices:
      v=mw@me.vertices[vi].co;an=math.degrees(math.atan2(v.y,v.x))%360;r=math.hypot(v.x,v.y)
      if 170<an<195 and v.z>15:
        k=int(r//3)*3;B[k][0]=min(B[k][0],an);B[k][1]=max(B[k][1],v.z)
for k in sorted(B):print('R',k,round(B[k][0],2),round(B[k][1],1))
