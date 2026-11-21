import bpy,sys,math
src=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
o=bpy.data.objects['gmhba'];M=o.matrix_world;names=[s.material.name for s in o.material_slots];best={}
for p in o.data.polygons:
  n=names[p.material_index]
  if not n.startswith(('tread','seat','wall')):continue
  c=M@p.center
  if c.z>3:continue
  a=int(math.degrees(math.atan2(c.y,c.x))//5);r=math.hypot(c.x,c.y)
  if r<best.get(a,(1e9,))[0]:best[a]=(r,c.x,c.y)
for a in sorted(best):print('RING',a*5,'%.1f %.1f %.1f'%best[a])
