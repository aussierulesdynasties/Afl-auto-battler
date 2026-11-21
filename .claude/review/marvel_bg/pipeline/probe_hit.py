"""Ray straight down at points ahead of the p5/p4 cameras: which object is on top, at what height."""
import bpy, mathutils
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for nm, (cx, cy) in {'p5': (-219.5, -181.9), 'p4': (-167.8, -162.7)}.items():
    d = mathutils.Vector((-cx, -cy, 0)).normalized()
    for t in (10, 30, 60, 100, 150):
        o = mathutils.Vector((cx, cy, 200)) + d * t
        hit, loc, nrm, idx, ob, mx = sc.ray_cast(dg, o, (0, 0, -1))
        print('PROBE', nm, t, round(o.x), round(o.y), ob.name if hit else None, round(loc.z, 2) if hit else None)
