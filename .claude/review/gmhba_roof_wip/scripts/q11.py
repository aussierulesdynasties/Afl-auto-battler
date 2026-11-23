import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
C=collections.defaultdict(list)
o=[o for o in bpy.data.objects if o.type=='MESH'][0];me=o.data;mw=o.matrix_world;mats=[s.material.name for s in o.material_slots]
for p in me.polygons:
  c=mw@p.center;an=math.degrees(math.atan2(c.y,c.x))%360;r=math.hypot(c.x,c.y)
  if 174<an<188 and r>84 and c.z>8:C[mats[p.material_index]].append((round(an,1),round(r),round(c.z,1)))
for k,v in C.items():print('M',k,len(v),min(v),max(v),sorted(v,key=lambda t:t[2])[-1])
