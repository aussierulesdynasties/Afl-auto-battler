# swap the texture session's adelaide_westback.glb into glb/adelaide.blend: every mesh object whose geometry differs takes the glb's mesh+materials
# blender -b ../glb/adelaide.blend -P mk_westback.py -- <westback.glb>
import bpy, sys, os
W = sys.argv[sys.argv.index('--') + 1]
old = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=W)
new = [o for o in bpy.data.objects if o not in before]
n = 0
for o in new:
    if o.type != 'MESH': continue
    base = o.name.split('.')[0]
    t = old.get(base)
    if t and base == 'stands':
        print('swap', base, len(t.data.polygons), '->', len(o.data.polygons), [m.name for m in o.data.materials if m])
        t.data = o.data; n += 1
        for m in o.data.materials:
            if m and 'west_back' in m.name: m.blend_method = 'CLIP' if hasattr(m, 'blend_method') else None
for o in new: bpy.data.objects.remove(o, do_unlink=True)
print('swapped', n)
assert n >= 1
bpy.ops.wm.save_mainfile()
