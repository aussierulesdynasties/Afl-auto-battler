import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
A=collections.Counter();U=collections.Counter()
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world;mats=[s.material.name for s in ob.material_slots]
  for p in me.polygons:
    c=mw@p.center;an=math.degrees(math.atan2(c.y,c.x))%360;r=math.hypot(c.x,c.y)
    if 120<an<185 and 86<r<99 and mats[p.material_index]=='aisle':A[round(an*2)/2]+=1
    if 120<an<185 and 86<r<99:U[mats[p.material_index]]+=1
print('AISLE',sorted(A.items()));print('UMAT',U)
