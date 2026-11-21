import bpy,sys
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
for m in bpy.data.materials:
    if not m.name.startswith('jss'):continue
    b=m.node_tree.nodes.get('Principled BSDF');im=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    print('M',m.name,im,tuple(round(x,2) for x in b.inputs['Base Color'].default_value),round(b.inputs['Roughness'].default_value,2),round(b.inputs['Metallic'].default_value,2),m.use_backface_culling)
