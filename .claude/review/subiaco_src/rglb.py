# blender -b --python rglb.py -- IN.glb CAM.json W H OUT.png [geo]
import bpy,sys,json,math
from mathutils import Vector,Matrix
a=sys.argv[sys.argv.index('--')+1:];IN,CF,W,H,OUT=a[0],a[1],int(a[2]),int(a[3]),a[4];geo=len(a)>5
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=IN)
cam=json.load(open(CF))['p']
cy_,sy_=math.cos(cam[3]),math.sin(cam[3]);cp,sp=math.cos(cam[4]),math.sin(cam[4]);cr,sr=math.cos(cam[5]),math.sin(cam[5])
f=Vector((cy_*cp,sy_*cp,sp));r=Vector((sy_,-cy_,0));u=r.cross(f);R0=r*cr+u*sr;R1=-r*sr+u*cr
cd=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cd);bpy.context.scene.collection.objects.link(co)
co.matrix_world=Matrix(((R0.x,R1.x,-f.x,cam[0]),(R0.y,R1.y,-f.y,cam[1]),(R0.z,R1.z,-f.z,cam[2]),(0,0,0,1)))
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.lens=cam[6]/W*36;cd.clip_end=20000
sc=bpy.context.scene;sc.camera=co;sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.color_type='RANDOM' if geo else 'TEXTURE';sc.display.shading.light='STUDIO'
sc.render.resolution_x=W;sc.render.resolution_y=H;sc.render.film_transparent=True;sc.render.filepath=OUT
bpy.ops.render.render(write_still=True)
