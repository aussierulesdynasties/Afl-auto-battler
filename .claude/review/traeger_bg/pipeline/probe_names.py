import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        bb = [o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box]
        xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
        print('OBJ', o.name, len(o.data.polygons), 'x %.0f..%.0f y %.0f..%.0f z %.1f..%.1f' % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)), [m.name for m in o.data.materials][:4])
