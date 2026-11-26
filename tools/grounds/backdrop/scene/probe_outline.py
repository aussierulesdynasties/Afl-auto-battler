"""Footprint of the ground model: max radius per 2-degree bearing bin (all meshes), for keeping the cut and rails off it.
blender -b -P probe_outline.py -- model.glb out.json"""
import bpy, sys, json, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
R = np.zeros(180)
import os
C = [float(v) for v in os.environ.get('FP_C', '0,0').split(',')]   # the model's own centre (spec fp_centre), when its origin is off the oval
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name.split('.')[0] in a[2:]: continue
    M = np.array(o.matrix_world)
    V = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    V = V @ M[:3, :3].T + M[:3, 3]
    V = V[V[:, 2] < 3.0]
    if not len(V): continue
    dx = V[:, 0] - C[0]; dy = V[:, 1] - C[1]
    r = np.hypot(dx, dy); b = (np.degrees(np.arctan2(dy, dx)) % 360 // 2).astype(int) % 180
    np.maximum.at(R, b, r)
json.dump([round(float(x), 2) for x in R], open(a[1], 'w'))
print('OUTLINE min', R.min(), 'max', R.max())
