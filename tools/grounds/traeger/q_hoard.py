import bpy
for o in bpy.data.objects:
    ms=[s.material.name for s in o.material_slots if s.material]
    if any(k in m for m in ms for k in ('hoard','sign','opt_','sponsor','tio')) or o.name.startswith(('fence_hoard','opt_')):print('HIT',o.name,ms)
