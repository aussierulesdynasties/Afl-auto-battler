# whole-glb swap: every mesh object in the glb replaces the same-named object's mesh+materials in adelaide.blend (glb materials kept), new ones are added
import bpy, sys
W = sys.argv[sys.argv.index('--') + 1]
old = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=W)
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in new:
    base = o.name.split('.')[0]; t = old.get(base)
    if t:
        print('swap', base, len(t.data.polygons), '->', len(o.data.polygons)); t.data = o.data; t.matrix_world = o.matrix_world.copy()
        bpy.data.objects.remove(o, do_unlink=True)
    else:
        o.name = base; o.parent = None; print('add', base)
for o in [o for o in bpy.data.objects if o not in before and o.name not in old and o.type != 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
print('objects', sorted(o.name for o in bpy.data.objects))
bpy.ops.wm.save_mainfile()
