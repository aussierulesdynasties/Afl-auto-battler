import bpy, sys, json, os
bpy.ops.wm.read_factory_settings(use_empty=True)
spec = json.load(open('spec/optus.json'))
bpy.ops.import_scene.gltf(filepath=os.path.normpath(spec['glb']))
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    mats = [m.name for m in o.data.materials if m]
    print('OBJ', o.name, 'x %.0f..%.0f y %.0f..%.0f z %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), mats[:3], len(o.data.polygons))
