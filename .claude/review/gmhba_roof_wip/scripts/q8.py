import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
S=collections.defaultdict(set)
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world;mats=[s.material.name for s in ob.material_slots]
  for p in me.polygons:
    if mats[p.material_index]!='tread':continue
    for i in p.vertices:
      v=mw@me.vertices[i].co;an=math.degrees(math.atan2(v.y,v.x))%360;r=math.hypot(v.x,v.y)
      for a0 in(140,143,146,149,154):
        if a0<=an<a0+0.5 and r>78:S[a0].add((round(r,1),round(v.z,2)))
for a in S:print(a,sorted(S[a])[::6])
