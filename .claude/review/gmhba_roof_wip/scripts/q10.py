import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
B=collections.defaultdict(list)
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world;mats=[s.material.name for s in ob.material_slots]
  print('OBJ',ob.name,len(me.polygons),mats)
  for p in me.polygons:
    mn=mats[p.material_index]
    if not mn.startswith('roof') and mn not in('fascia','under'):continue
    for i in p.vertices:
      v=mw@me.vertices[i].co;an=math.degrees(math.atan2(v.y,v.x))%360;r=math.hypot(v.x,v.y)
      if 176<an<186:B[int(r//4)*4].append((round(an,2),round(v.z,1),mn))
for k in sorted(B):
  L=sorted(B[k]);print('R',k,L[0],L[len(L)//2],L[-1])
