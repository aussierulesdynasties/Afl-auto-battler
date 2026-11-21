import bpy,sys,json
from mathutils import Matrix,Vector
a=sys.argv[sys.argv.index('--')+1:];src,cj=a[0],a[1];px=json.loads(a[2])
J=json.load(open(cj));bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
R=Matrix(J['R']);C=Vector(J['C']);f=J['f'];cx=J['cx'];cy=J['cy']
dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene
for u,v in px:
  d=(R.transposed()@Vector(((u-cx)/f,(v-cy)/f,1))).normalized()
  ok,loc,n,fi,ob,_=sc.ray_cast(dg,C,d)
  if ok:
    me=ob.data;mi=me.polygons[fi].material_index;print('HIT',u,v,ob.name,me.materials[mi].name,'%.1f %.1f %.1f'%tuple(loc),'n %.2f %.2f %.2f'%tuple(n))
  else:print('HIT',u,v,'none')
