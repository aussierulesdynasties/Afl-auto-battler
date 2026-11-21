import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.3,0.3,0.3);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;s.rotation_euler=(0.5,0.2,0.9);sc.collection.objects.link(s)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1400;sc.render.resolution_y=1400
c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.type='ORTHO';c.data.ortho_scale=300;c.location=(0,0,300);c.rotation_euler=(0,0,0);sc.collection.objects.link(c)
sc.camera=c;sc.render.filepath=a[1];bpy.ops.render.render(write_still=True)
