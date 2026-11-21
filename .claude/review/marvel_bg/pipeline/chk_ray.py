import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for x in range(180, 300, 8):
    for y in (-80, -40, 0, 40):
        hit, loc, nor, idx, ob, _ = sc.ray_cast(dg, Vector((x, y, 300)), Vector((0, 0, -1)))
        if hit and not ob.name.startswith(('bg_rail', 'bg_near_ground')): print('HIT', x, y, ob.name, round(loc.z, 2))
