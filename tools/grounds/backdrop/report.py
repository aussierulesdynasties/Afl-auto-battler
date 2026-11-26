"""Where a backdrop's triangles and draws go: per family (name without slice and variant suffixes),
its pieces and triangles, biggest first, and the images with their sizes.
   blender -b --python report.py -- a_part1.glb [a_part2.glb ...]
"""
import bpy, sys, re, collections
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in a: bpy.ops.import_scene.gltf(filepath=f)
n = collections.Counter(); t = collections.Counter()
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    k = re.sub(r'(_s\d+.*|_v\d+|_joined|\.\d+)+$', '', o.name)
    n[k] += 1; t[k] += sum(len(p.vertices) - 2 for p in o.data.polygons)
print('REPORT total tris', sum(t.values()), 'pieces', sum(n.values()))
for k, v in t.most_common(25): print('REPORT %8d tris %3d pieces %s' % (v, n[k], k))
for im in sorted(bpy.data.images, key=lambda i: -i.size[0] * i.size[1])[:12]:
    print('REPORT image', im.name, tuple(im.size), im.channels)
