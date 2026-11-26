import os, bpy, sys, math, mathutils
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
R = mathutils.Matrix.Rotation(math.radians(float(a[2])), 4, 'Z')
for o in bpy.data.objects:
    if o.parent is None: o.matrix_world = R @ o.matrix_world
bpy.ops.export_scene.gltf(filepath=a[1], export_format='GLB')
