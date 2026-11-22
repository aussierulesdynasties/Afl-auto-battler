import bpy
for o in bpy.data.objects:
    if o.name.startswith(('bg_roof','bg_road','bg_bld_tower')): print('OBJ', o.name, len(o.data.polygons), [m.name for m in o.data.materials])
