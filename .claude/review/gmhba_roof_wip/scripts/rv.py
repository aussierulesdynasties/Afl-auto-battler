import bpy,math,mathutils,sys
a=sys.argv[sys.argv.index('--')+1:];src,out=a[0],a[1];views=[tuple(map(float,v.split(','))) for v in a[2:]]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=src)
sc=bpy.context.scene;w=bpy.data.worlds.new('w');w.color=(0.6,0.7,0.85);sc.world=w
s=bpy.data.objects.new('s',bpy.data.lights.new('s','SUN'));s.data.energy=4;s.rotation_euler=(0.7,0.2,0.9);sc.collection.objects.link(s)
f=bpy.data.objects.new('f',bpy.data.lights.new('f','SUN'));f.data.energy=2.5;f.rotation_euler=(0.8,-0.3,-2.3);sc.collection.objects.link(f)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1600;sc.render.resolution_y=1000
for i,(x,y,z,tx,ty,tz,lens) in enumerate(views):
    c=bpy.data.objects.new('c',bpy.data.cameras.new('c'));c.data.lens=lens;c.data.clip_end=5000;sc.collection.objects.link(c)
    c.location=(x,y,z);d=mathutils.Vector((tx,ty,tz))-c.location
    c.rotation_euler=d.to_track_quat('-Z','Y' if abs(d.normalized().z)<0.99 else 'Y').to_euler()
    sc.camera=c;sc.render.filepath=out+"_%d.png"%i;bpy.ops.render.render(write_still=True)
