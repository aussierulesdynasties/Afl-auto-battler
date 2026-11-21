import bpy
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.name.startswith('bg_bld') or o.name.startswith('bg_roof_plant') or o.name.startswith('bg_station'):
        m = o.data.materials[0] if o.data.materials else None
        img = [n.image.name for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image] if m else []
        ca = o.data.color_attributes
        print(o.name, len(o.data.polygons), m.name if m else None, img, [a.name for a in ca])
