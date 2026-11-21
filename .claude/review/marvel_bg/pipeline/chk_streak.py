"""Locate the rail yard (densest bg_rail_bed area) and list other objects with faces there, by area."""
import bpy, collections
import numpy as np
o = bpy.data.objects['bg_rail_bed']
P = np.array([tuple(o.matrix_world @ p.center) for p in o.data.polygons])
H, xe, ye = np.histogram2d(P[:, 0], P[:, 1], bins=30)
i, j = np.unravel_index(H.argmax(), H.shape); cx, cy = (xe[i] + xe[i + 1]) / 2, (ye[j] + ye[j + 1]) / 2
print('YARD', round(cx), round(cy))
C = collections.Counter()
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.name.startswith('bg_rail'): continue
    M = ob.matrix_world
    for p in ob.data.polygons:
        c = M @ p.center
        if abs(c.x - cx) < 120 and abs(c.y - cy) < 120: C[ob.name] += p.area
for k, v in C.most_common(20): print('OBJ', k, round(v))
