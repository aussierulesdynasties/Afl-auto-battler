import bpy,sys,math
from mathutils import Vector
out=sys.argv[sys.argv.index('--')+1];sc=bpy.context.scene
cam=bpy.data.objects.new('bc',bpy.data.cameras.new('bc'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.lens=35
eye=Vector((-30.4+20,-8.8,18));tgt=Vector((-30.4-90,-8.8-10,14))
cam.location=eye;cam.rotation_euler=(tgt-eye).to_track_quat('-Z','Y').to_euler()
if not any(o.type=='LIGHT' for o in sc.objects):
    l=bpy.data.objects.new('sun',bpy.data.lights.new('sun','SUN'));l.data.energy=4;l.rotation_euler=(0.7,0.2,0.8);sc.collection.objects.link(l)
sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x,sc.render.resolution_y=1600,900;sc.render.filepath=out;bpy.ops.render.render(write_still=True)
