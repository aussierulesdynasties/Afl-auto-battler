import bpy
from mathutils import Vector
for o in bpy.context.scene.objects:
    if o.type not in ('MESH','VOLUME','CURVE'): print('OBJ',o.name,o.type); continue
    bb=[o.matrix_world@Vector(c) for c in o.bound_box]
    x0=min(b.x for b in bb);x1=max(b.x for b in bb);y0=min(b.y for b in bb);y1=max(b.y for b in bb);z1=max(b.z for b in bb)
    if x0<95 and x1>80 and y0<0 and y1>-20: print('OBJ',o.name,o.type,round(x0),round(x1),round(y0),round(y1),round(z1),o.visible_get(), [m.material.name for m in o.material_slots if m.material][:4])
