import bpy, collections
C = collections.Counter()
for o in bpy.data.objects:
    if o.type == 'MESH': C[o.name.split('.')[0][:28]] += len(o.data.polygons)
for k in sorted(C):
    if any(s in k for s in ('roof', 'parapet', 'kerb', 'bld_tower', 'bld_block', 'rail_bed', 'plant')): print(k, C[k])
for m in bpy.data.materials:
    if 'roof' in m.name or 'parapet' in m.name: print('MAT', m.name, [n.image.name for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'])
