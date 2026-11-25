"""Footprint of the ground model without its square base. Step 1 (Blender): faces below 3 m -> polys json.
blender -b -P fence_mask.py -- model.glb polys.json base_name [...]
Step 2 (plain Python): python fence_mask.py polys.json mask.npy -> 0.5 m grid (+-260 m), filled, grown 2 m, holes filled."""
import sys, json
if '--' in sys.argv:
    import bpy
    a = sys.argv[sys.argv.index('--') + 1:]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=a[0])
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name.split('.')[0] in a[2:]: continue
        M = o.matrix_world; V = [M @ v.co for v in o.data.vertices]
        for p in o.data.polygons:
            q = [V[i] for i in p.vertices]
            if min(v.z for v in q) <= 3.0: out.append([[round(v.x, 2), round(v.y, 2)] for v in q])
    json.dump(out, open(a[1], 'w')); print('POLYS', len(out))
else:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    R, S = 260.0, 0.5; N = int(2 * R / S)
    im = Image.new('L', (N, N), 0); dr = ImageDraw.Draw(im)
    for q in json.load(open(sys.argv[1])):
        dr.polygon([((x + R) / S, (R - y) / S) for x, y in q], fill=255, outline=255)
    im = im.filter(ImageFilter.MaxFilter(33))         # grow 8 m: closes gate gaps in the fence
    ImageDraw.floodfill(im, (0, 0), 128)              # outside
    m = Image.fromarray(((np.asarray(im) != 128) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(25))   # shrink 6 m back: net 2 m past the model
    m = np.asarray(m) > 0
    np.save(sys.argv[2], m); print('MASK', m.sum() * S * S, 'm2')
