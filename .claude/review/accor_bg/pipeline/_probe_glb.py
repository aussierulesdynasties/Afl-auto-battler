import bpy
ms=[o for o in bpy.data.objects if o.type=='MESH']
print('NOBJ',len(ms)); import mathutils
for o in sorted(ms,key=lambda o:-max(o.dimensions))[:40]:
    c=[o.matrix_world@mathutils.Vector(v) for v in o.bound_box]
    print('OBJ',o.name,[round(min(p[i] for p in c)) for i in range(3)],[round(max(p[i] for p in c)) for i in range(3)],o.hide_render)
