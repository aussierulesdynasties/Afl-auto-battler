import bpy, math
from mathutils import Vector
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
pos = Vector((0, -520, 190)); look = Vector((0, 0, 10)); R = (look - pos).to_track_quat("-Z", "Y").to_matrix(); t = math.tan(math.radians(30))
for (u, v) in [(1000, 60), (1100, 90), (900, 100)]:
    d = R @ Vector(((u - 640) / 640 * t, (360 - v) / 640 * t, -1)); d.normalize()
    hit, loc, n, i, ob, m = sc.ray_cast(dg, pos, d)
    print('RAY', u, v, ob.name if hit else None, [round(c) for c in loc] if hit else '', ob.active_material.name if hit and ob.active_material else '')
for o in bpy.data.objects:
    if 'water' in o.name or 'sea' in o.name: print('OBJ', o.name, o.hide_render, [s.material.name for s in o.material_slots], round(o.location.z, 1), len(o.data.vertices))
for mn in ('far_water',):
    m = bpy.data.materials.get(mn)
    if m:
        b = m.node_tree.nodes['Principled BSDF']; print('MAT', mn, 'spec', b.inputs['Specular IOR Level'].default_value, 'rough', b.inputs['Roughness'].default_value)
        for l in m.node_tree.links: print('  LINK', l.from_node.name, '->', l.to_node.name, l.to_socket.name)
