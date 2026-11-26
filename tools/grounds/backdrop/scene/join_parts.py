import os, bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in a[1:]: bpy.ops.import_scene.gltf(filepath=f)
bpy.ops.export_scene.gltf(filepath=a[0], export_format='GLB')
