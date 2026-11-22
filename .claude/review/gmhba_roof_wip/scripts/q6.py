import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
C=collections.Counter();box=[]
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world
  for p in me.polygons:
    mn=ob.material_slots[p.material_index].material.name
    c=mw@p.center;an=math.degrees(math.atan2(c.y,c.x))%360;r=math.hypot(c.x,c.y)
    if 140<an<158:C[(mn,int(r//10)*10)]+=1
    if mn=='cream' and 160<an<185 and r>100:box.append((round(an,1),round(r,1),round(c.z,1),round(p.area,1)))
for k in sorted(C):print(k,C[k])
print('CREAM',len(box),sorted(box)[:40])
