import bpy, mathutils, math, sys
sc = bpy.context.scene
cam = bpy.data.objects.new('fc_cam', bpy.data.cameras.new('fc_cam')); sc.collection.objects.link(cam); sc.camera = cam
tgt = mathutils.Vector((175, -10, 5))
for i, (eye, out) in enumerate([((300, -170, 120), 'fc_close_a.png'), ((175, -10, 260), 'fc_close_top.png')]):
    cam.location = eye
    cam.rotation_euler = (tgt - mathutils.Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 35
    sc.render.resolution_x = 1600; sc.render.resolution_y = 900; sc.render.resolution_percentage = 100
    sc.render.filepath = '//../../' + out if False else bpy.path.abspath('//') + out
    bpy.ops.render.render(write_still=True)
    print('saved', out)
