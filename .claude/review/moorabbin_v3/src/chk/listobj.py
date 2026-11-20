import bpy
from mathutils import Vector
for o in bpy.data.objects:
    if o.type!='MESH':continue
    bb=[o.matrix_world@Vector(c) for c in o.bound_box]
    mn=[round(min(v[i] for v in bb),1) for i in range(3)];mx=[round(max(v[i] for v in bb),1) for i in range(3)]
    print('OBJ',o.name,mn,mx,len(o.data.polygons))
