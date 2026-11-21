import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
S=collections.defaultdict(list)
for ob in bpy.data.objects:
  if ob.type!='MESH':continue
  me=ob.data;mw=ob.matrix_world;mats=[s.material.name for s in ob.material_slots]
  for p in me.polygons:
    if mats[p.material_index]!='tread':continue
    for i in p.vertices:
      v=mw@me.vertices[i].co;an=math.degrees(math.atan2(v.y,v.x))%360;r=math.hypot(v.x,v.y)
      if 132<an<166:S[int(an)].append((r,v.z))
for a in sorted(S):
  L=S[a];mx=max(L,key=lambda t:t[1]);up=[t for t in L if t[1]>12]
  rmin=min(t[0] for t in up) if up else 0
  print(a,'n',len(L),'zmax',round(mx[1],1),'r@zmax',round(mx[0],1),'upper rmin',round(rmin,1),'upper zmin',round(min([t[1] for t in up] or [0]),1))
