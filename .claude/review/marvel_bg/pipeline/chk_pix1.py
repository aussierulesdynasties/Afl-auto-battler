"""Ray from the frame-151 orbit camera through pixels of the white yard lines; print what they hit (incl. ground)."""
import bpy, math
from mathutils import Vector
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
W, H, fov = 1280, 720, math.radians(60)
a = math.radians(90) + 2 * math.pi * 0 / 240
look = Vector((0, 0, 10)); pos = Vector((600 * math.cos(a), 600 * math.sin(a), 450))
q = (look - pos).to_track_quat('-Z', 'Y')
fx = math.tan(fov / 2)
for px, py in [(880, 620), (470, 180), (330, 160), (40, 560), (1100, 110), (980, 140), (700, 150), (1220, 90)]:
    d = q @ Vector(((px / W * 2 - 1) * fx, -(py / H * 2 - 1) * fx * H / W, -1)); d.normalize()
    hit, loc, nor, idx, ob, _ = sc.ray_cast(dg, pos, d)
    if not hit: print('PIX', px, py, 'miss'); continue
    m = ob.data.materials[ob.data.polygons[idx].material_index] if ob.data.materials else None
    print('PIX', px, py, ob.name, m.name if m else None, tuple(round(c) for c in loc))
