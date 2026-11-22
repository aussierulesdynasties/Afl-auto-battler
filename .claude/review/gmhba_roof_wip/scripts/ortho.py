import bpy,sys,math
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1];cx,cy,w,h,ppm=map(float,a[2:7])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE'
sc.render.resolution_x,sc.render.resolution_y=int(w*ppm),int(h*ppm)
cam=bpy.data.objects.new('c',bpy.data.cameras.new('c'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=max(w,h);cam.location=(cx,cy,300);cam.rotation_euler=(0,0,0);cam.data.clip_end=1000
sc.world=bpy.data.worlds.new('w');sc.world.color=(0,0,0)
sc.render.filepath=out;bpy.ops.render.render(write_still=True)
