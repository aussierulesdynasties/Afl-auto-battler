import bpy, sys
fix = '--fix' in sys.argv
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and any(k in n.image.name.lower() for k in ('seat', 'aisle')):
            print('IMG', m.name, n.image.name, n.interpolation, n.image.size[:])
            if fix: n.interpolation = 'Linear'
if fix: bpy.ops.wm.save_mainfile(); print('saved')
