import bpy, sys
p = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    if not vs: continue
    xs=[v.x for v in vs]; ys=[v.y for v in vs]
    if max(xs)-min(xs) > 100: print('BB', o.name, round((max(xs)+min(xs))/2,1), round((max(ys)+min(ys))/2,1), round(max(xs)-min(xs)), round(max(ys)-min(ys)))
