import bpy,math,mathutils,sys
from bpy_extras.view3d_utils import region_2d_to_vector_3d
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+'optus_roof11.glb')
sc=bpy.context.scene;sc.render.resolution_x=1600;sc.render.resolution_y=900
dg=bpy.context.evaluated_depsgraph_get()
def cam(a,r,h,tr,lens):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=lens;sc.collection.objects.link(c)
    A=math.radians(a);c.location=(r*math.cos(A)-30,r*math.sin(A)-9,h)
    t=mathutils.Vector((tr*math.cos(A)-30,tr*math.sin(A)-9,30));c.rotation_euler=(t-c.location).to_track_quat('-Z','Y').to_euler();return c
def ray(c,px,py):
    bpy.context.view_layer.update()
    fr=c.data.view_frame(scene=sc);M=c.matrix_world
    tr_,br,bl,tl=[M@v for v in fr]
    u,v=px/1600,py/900;p=tl+(tr_-tl)*u+(bl-tl)*v;d=(p-c.location).normalized()
    hit,loc,n,fi,ob,_=sc.ray_cast(dg,c.location,d)
    if hit:
        mi=ob.data.polygons[fi].material_index;print('HIT',px,py,ob.name,ob.data.materials[mi].name,tuple(round(x,1) for x in loc))
c1=cam(-60,250,90,120,50)
for p in((470,298),(490,300),(520,296),(1150,312),(1170,316),(1440,322),(1460,318),(700,292)):ray(c1,*p)
c2=cam(30,330,140,0,40)
for y in range(536,550,2):
    for x in(38,40,42,44,46):ray(c2,x,y)
