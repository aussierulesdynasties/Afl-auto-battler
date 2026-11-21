import bpy
o = bpy.data.objects['east_wall']; print('PARENT', o.parent.name if o.parent else None)
for v in o.data.vertices: print('V', tuple(round(c, 1) for c in o.matrix_world @ v.co))
