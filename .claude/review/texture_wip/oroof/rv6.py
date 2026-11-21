import bpy,math,mathutils,sys
O=sys.argv[-2];G=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+G+'.glb')
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.75,0.82,0.95);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;s.rotation_euler=(0.7,0,-1.0);sc.collection.objects.link(s)
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=96;sc.render.resolution_x=1600;sc.render.resolution_y=900;sc.cycles.use_denoising=True
for i,(a,r,h,tr,lens) in enumerate(((-60,420,200,0,35),(-60,250,90,120,50),(30,330,140,0,40))):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=lens;sc.collection.objects.link(c)
    A=math.radians(a);c.location=(r*math.cos(A)-30,r*math.sin(A)-9,h)
    tgt=mathutils.Vector((tr*math.cos(A)-30,tr*math.sin(A)-9,30))
    c.rotation_euler=(tgt-c.location).to_track_quat('-Z','Y').to_euler();sc.camera=c
    sc.render.filepath=O+G+"_f%d.png"%i;bpy.ops.render.render(write_still=True)
