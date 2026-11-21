import bpy, math, sys, json
from mathutils import Vector
fr, pts = int(sys.argv[-2]), json.loads(sys.argv[-1])
a = math.radians(90) + 2*math.pi*(fr-1)/240; look = Vector((0,0,10))
c = Vector((520*math.cos(a), 520*math.sin(a), 190)); q = (look-c).to_track_quat("-Z","Y")
f = 640/math.tan(math.radians(30)); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for px, py in pts:
    d = q @ Vector(((px-640)/f, -(py-360)/f, -1)).normalized()
    ok, loc, n, i, ob, m = sc.ray_cast(dg, c, d)
    mat = ob.material_slots[ob.data.polygons[i].material_index].material.name if ok and ob.material_slots else None
    print('HIT', px, py, ob.name if ok else None, mat, [round(v,1) for v in loc])
