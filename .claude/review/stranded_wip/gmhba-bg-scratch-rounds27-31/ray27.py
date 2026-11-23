import bpy, math
from mathutils import Vector
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
pos = Vector((0, -520, 190)); look = Vector((0, 0, 10))
q = (look - pos).to_track_quat("-Z", "Y"); R = q.to_matrix()
t = math.tan(math.radians(30))
for (u, v) in [(820, 6), (900, 8), (1000, 6), (1100, 10), (1200, 4), (1250, 12)]:
    d = R @ Vector(((u - 640) / 640 * t, (360 - v) / 640 * t, -1)); d.normalize()
    hit, loc, n, i, ob, m = sc.ray_cast(dg, pos, d)
    print('RAY', u, v, ob.name if hit else None, [round(c) for c in loc] if hit else '', round((loc - pos).length) if hit else '')
