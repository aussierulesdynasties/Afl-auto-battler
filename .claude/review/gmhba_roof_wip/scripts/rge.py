import bpy,sys,math
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1];lx,ly,lz,rng,hd,tl,fov=map(float,a[2:9])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x,sc.render.resolution_y=1280,471
h,t=math.radians(hd),math.radians(tl);L=Vector((lx,ly,lz))
d=Vector((math.sin(h)*math.sin(t),math.cos(h)*math.sin(t),-math.cos(t)))
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam
cam.location=L-d*rng;cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
cam.data.sensor_fit='HORIZONTAL';cam.data.angle=math.radians(fov);cam.data.clip_end=5000
sc.world=bpy.data.worlds.new('w');sc.world.color=(0.6,0.7,0.8)
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
