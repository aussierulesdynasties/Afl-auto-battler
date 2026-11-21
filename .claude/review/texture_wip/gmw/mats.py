import bpy,sys
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"gmhba_tex.glb")
for o in bpy.data.objects:
    if o.type!='MESH':continue
    bb=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box]
    xs=[v.x for v in bb];ys=[v.y for v in bb];zs=[v.z for v in bb]
    ms=[s.material.name if s.material else '-' for s in o.material_slots]
    print("OBJ",o.name,"x%.0f..%.0f y%.0f..%.0f z%.0f..%.0f"%(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)),ms)
for m in bpy.data.materials:
    imgs=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.node_tree else []
    print("MAT",m.name,imgs)
