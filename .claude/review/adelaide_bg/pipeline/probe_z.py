import bpy, sys
p = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    if vs: print('Z', o.name, round(min(v.z for v in vs),2), round(max(v.z for v in vs),2), len(vs))
