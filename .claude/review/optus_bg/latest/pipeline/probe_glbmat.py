import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for m in bpy.data.materials:
    if not m.node_tree: continue
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeTexImage' and n.image:
            print('MAT', m.name, n.image.name, [l.to_socket.name + '@' + l.to_node.name for l in n.outputs[0].links + n.outputs[1].links], n.image.colorspace_settings.name)
