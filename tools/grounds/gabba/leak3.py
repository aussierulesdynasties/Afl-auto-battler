import bpy, math, mathutils as mu
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
az, el = math.radians(-12), math.radians(20)
d = mu.Vector((math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)))
for x in [x/2 for x in range(80, 100)]:
    o = mu.Vector((x, -4, 0.1)); hit = sc.ray_cast(dg, o, d)[0]
    if not hit:
        pts = []
        for X in range(70, 124, 3):
            t = (X - x) / d.x; p = o + d * t; r = math.hypot(p.x - 2.47, p.y + 3.47); pts.append('r%.0f z%.1f' % (r, p.z))
        print('LIT', x, ' '.join(pts))
