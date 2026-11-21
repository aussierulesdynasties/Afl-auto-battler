import bpy, sys
from mathutils import Vector
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    me = o.data; M = o.matrix_world; hit = 0
    for v in me.vertices:
        w = M @ v.co
        if 80 < w.x < 140 and 30 < w.y < 100 and w.z > 0.5: hit += 1
    if hit: print('OBJ', o.name, hit, len(me.vertices))
