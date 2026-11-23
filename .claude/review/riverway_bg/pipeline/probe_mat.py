import bpy, sys
p = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=p)
for m in bpy.data.materials:
    if 'grass' not in m.name.lower(): continue
    b = m.node_tree.nodes.get('Principled BSDF')
    tex = [n.image.name + ' %dx%d' % tuple(n.image.size) for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    print('MAT', m.name, 'rough', round(b.inputs['Roughness'].default_value, 2), 'spec', round(b.inputs['Specular IOR Level'].default_value, 2), 'base', [round(c, 3) for c in b.inputs['Base Color'].default_value[:3]], tex)
