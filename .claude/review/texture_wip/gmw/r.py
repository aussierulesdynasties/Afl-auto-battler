import bpy,math,mathutils,sys
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"gmhba_tex2.glb")
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.6,0.7,0.85);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;s.rotation_euler=(0.8,0,0.9);sc.collection.objects.link(s)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1920;sc.render.resolution_y=1080
for i,(r,a,h,tz) in enumerate(((210,30,70,10),(90,200,12,12),(90,300,12,12))):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=35;sc.collection.objects.link(c)
    c.location=(r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),h)
    c.rotation_euler=(mathutils.Vector((0,0,tz))-c.location).to_track_quat('-Z','Y').to_euler()
    sc.camera=c;sc.render.filepath=O+"w%d.png"%i;bpy.ops.render.render(write_still=True)
