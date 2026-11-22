import bpy
sc = bpy.context.scene
print('AA', sc.eevee.taa_render_samples, 'filter', sc.render.filter_size)
for o in bpy.data.objects:
    if o.type == 'MESH' and any(s.material and s.material.name.startswith(('seats','aisle')) for s in o.material_slots):
        print('OBJ', o.name, len(o.data.polygons), [s.material.name for s in o.material_slots if s.material][:6])
