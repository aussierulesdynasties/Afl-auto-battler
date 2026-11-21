import bpy,math,mathutils,sys
from bpy_extras.view3d_utils import region_2d_to_vector_3d
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+'optus_roof6.glb')
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
for p in((420,245),(700,255),(900,250),(1250,255),(600,262),(1000,265)):ray(c1,*p)
c2=cam(30,330,140,0,40)
import builtins
_r=ray
def ray(c,x,y):_r(c,280+x/3,330+y/3)
for p in((165,330),(176,383),(162,452),(225,508),(302,568),(170,329),(166,331)):ray(c2,*p)
