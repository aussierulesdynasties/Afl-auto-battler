import bpy,sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
for o in bpy.data.objects:
    if o.type!='MESH':continue
    me=o.data
    print("OBJ",o.name,len(me.polygons),[m.name for m in me.materials])
for m in bpy.data.materials:
    imgs=[n.image.name+str(tuple(n.image.size)) for n in (m.node_tree.nodes if m.node_tree else []) if n.type=='TEX_IMAGE']
    print("MAT",m.name,imgs)
