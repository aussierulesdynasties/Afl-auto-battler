import bpy
for m in bpy.data.materials:
    if m.name.startswith('apron'):
        print('MAT', m.name, [n.image.name + ' ' + str(tuple(n.image.size)) for n in m.node_tree.nodes if n.type == 'TEX_IMAGE'])
