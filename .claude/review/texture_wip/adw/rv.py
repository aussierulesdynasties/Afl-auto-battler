import bpy,math,mathutils,sys
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"adelaide_westback.glb")
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.6,0.7,0.85);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;s.rotation_euler=(0.9,0,-1.2);sc.collection.objects.link(s)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.cycles.use_denoising=False
for i,(a,r,h,tr) in enumerate(((-70,330,60,120),(-80,175,3,128))):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=35;sc.collection.objects.link(c)
    A=math.radians(a);c.location=(r*math.cos(A),r*math.sin(A),h)
    tgt=mathutils.Vector((tr*math.cos(A),tr*math.sin(A),18))
    c.rotation_euler=(tgt-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c
    sc.render.filepath=O+"chk%d.png"%i;bpy.ops.render.render(write_still=True)
