import bpy,sys
O=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"orig.glb")
import collections
d=collections.Counter()
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for s in o.material_slots:
        if s.material: d[(s.material.name)]+=1
for o in bpy.data.objects:
    if o.type=='MESH' and (o.dimensions.z>15 or 'west' in o.name.lower()):
        print("OBJ",o.name,[round(v,1) for v in o.dimensions],[s.material.name for s in o.material_slots if s.material][:6],round(o.location.x),round(o.location.y))
for m in bpy.data.materials:
    ims=[n.image.name+str(tuple(n.image.size)) for n in (m.node_tree.nodes if m.node_tree else []) if n.type=='TEX_IMAGE' and n.image]
    print("MAT",m.name,ims)
