import bpy
print('OBJS', sorted(o.name for o in bpy.data.objects if o.name.startswith(('bg_bld','bg_car','bg_rail','bg_court_f','bg_roads'))))
