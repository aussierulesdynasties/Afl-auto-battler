import bpy, math
from mathutils import Vector
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
pos = Vector((185, -115.26, 55)); look = Vector((130, -20, 3))
q = (look - pos).to_track_quat("-Z", "Y"); R = q.to_matrix()
t = math.tan(math.radians(25))
for (u, v) in [(60,450),(200,500),(350,450),(150,650),(450,380),(700,450)]:
    d = R @ Vector(((u - 640) / 640 * t, (360 - v) / 640 * t, -1)); d.normalize()
    hit, loc, n, i, ob, m = sc.ray_cast(dg, pos, d)
    print('RAY', u, v, ob.name if hit else None, [round(c) for c in loc] if hit else '', round((loc - pos).length) if hit else '')
