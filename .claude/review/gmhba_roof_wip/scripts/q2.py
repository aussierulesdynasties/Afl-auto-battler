import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
C=collections.defaultdict(list)
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world
  for p in me.polygons:
    c=mw@p.center;an=math.degrees(math.atan2(c.y,c.x));r=math.hypot(c.x,c.y)
    if 174<an<186 and c.z>12 and r>80:
      C[(ob.name,ob.material_slots[p.material_index].material.name,int(an))].append((round(r),round(c.z,1)))
for k,v in sorted(C.items()):print('Q',k,len(v),min(v),max(v))
