import bpy,sys
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+'optus_roof11.glb')
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='MATERIAL'
sc.view_settings.view_transform='Standard';sc.render.resolution_x=2000;sc.render.resolution_y=1840
for m in bpy.data.materials:m.diffuse_color=(1,1,1,1) if m.name in('roof_bay','roof_edge') else (0,0,0,1)
sc.world=bpy.data.worlds.new('w');sc.world.color=(0,0,0)
c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.type='ORTHO';c.data.ortho_scale=500;c.data.clip_end=1000;c.data.sensor_fit='HORIZONTAL';sc.collection.objects.link(c)
c.location=(-10,0,300);c.rotation_euler=(0,0,0);sc.camera=c
sc.render.filepath=O+'top_mask.png';bpy.ops.render.render(write_still=True)
