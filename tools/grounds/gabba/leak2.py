import bpy, math, mathutils as mu
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
az, el = math.radians(-12), math.radians(20)
d = mu.Vector((math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), math.sin(el)))
for y in range(84, -90, -8):
    row = ''
    for x in range(-100, 104, 4):
        if (x/88)**2 + ((y+3)/76)**2 > 1: row += ' '; continue
        hit = sc.ray_cast(dg, mu.Vector((x, y, 0.1)), d)[0]; row += '#' if hit else '.'
    print('ROW %4d %s' % (y, row))
