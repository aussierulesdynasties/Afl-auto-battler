import bpy,sys,math,json
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];L=json.load(open(a[0]))
sc=bpy.context.scene;cam=bpy.data.cameras.new('c');co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co)
sc.camera=co;sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='AgX';cam.clip_end=3000
for s in L:
    eye=Vector(s['eye']);at=Vector(s['at']);co.location=eye;co.rotation_euler=(at-eye).to_track_quat('-Z','Y').to_euler();cam.lens=s.get('lens',30)
    sc.render.resolution_x,sc.render.resolution_y=s.get('res',[1920,1080]);sc.render.filepath=s['out'];bpy.ops.render.render(write_still=True)
