"""Top-down plan of a ground model (roof and stand cover above 2 m), 1 m/px, 700 x 700 centred on the model origin,
x east (model x), rows north up (model -z). usage: python model_plan.py model.glb out.npy"""
import os, bpy, sys, numpy as np
from PIL import Image, ImageDraw
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
N = 700; im = Image.new('L', (N, N), 0); dr = ImageDraw.Draw(im)
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    M = np.array(o.matrix_world); V = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', V); V = V.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    o.data.calc_loop_triangles(); T = np.empty(len(o.data.loop_triangles) * 3, int); o.data.loop_triangles.foreach_get('vertices', T); T = T.reshape(-1, 3)
    P = V[T]   # blender: x east, y north, z up
    keep = P[:, :, 2].max(1) > 2.0
    for t in P[keep]:
        dr.polygon([(x + N / 2, N / 2 - y) for x, y, z in t], fill=255)
np.save(a[1], np.asarray(im) > 0)
print('PLAN', (np.asarray(im) > 0).sum())
