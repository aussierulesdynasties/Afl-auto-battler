import bpy,sys,math
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world
  for p in me.polygons:
    mn=ob.material_slots[p.material_index].material.name
    if not mn.startswith('jss'):continue
    vs=[mw@me.vertices[i].co for i in p.vertices]
    ans=[math.degrees(math.atan2(v.y,v.x)) for v in vs]
    if min(ans)<130.5 and p.area>0.5:print('F',mn,[ (round(math.hypot(v.x,v.y),1),round(a,1),round(v.z,1)) for v,a in zip(vs,ans)])
