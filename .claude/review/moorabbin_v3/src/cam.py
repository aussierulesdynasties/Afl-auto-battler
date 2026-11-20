# blender -b moorabbin3.blend --python cam.py -- out.png ex ey ez tx ty tz lens px [out2 ex ey ez tx ty tz lens px ...]
import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];sc=bpy.context.scene
cam=bpy.data.cameras.new('c');cam.clip_start=0.1;cam.clip_end=3000;co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co);sc.camera=co
sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard';sc.render.image_settings.file_format='PNG'
for i in range(0,len(a),9):
    out=a[i];e=Vector(map(float,a[i+1:i+4]));t=Vector(map(float,a[i+4:i+7]));cam.lens=float(a[i+7]);px=int(a[i+8])
    co.location=e;co.rotation_euler=(t-e).to_track_quat('-Z','Y').to_euler()
    sc.render.resolution_x=px;sc.render.resolution_y=px*2//3;sc.render.filepath=out;bpy.ops.render.render(write_still=True);print('CAM',out)
