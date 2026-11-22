# add the glb's 'west_concourse' object (recess + ceiling behind the alpha-cut arches) to glb/adelaide.blend, unchanged
import bpy, sys
W = sys.argv[sys.argv.index('--') + 1]
assert 'west_concourse' not in bpy.data.objects
before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=W)
new = [o for o in bpy.data.objects if o not in before]; keep = 0
for o in new:
    if o.name.split('.')[0] == 'west_concourse' and o.type == 'MESH':
        o.name = 'west_concourse'; o.parent = None; keep += 1; print('kept', o.name, len(o.data.polygons), [m.name for m in o.data.materials if m])
for o in new:
    if o.name != 'west_concourse': bpy.data.objects.remove(o, do_unlink=True)
assert keep == 1; bpy.ops.wm.save_mainfile()
