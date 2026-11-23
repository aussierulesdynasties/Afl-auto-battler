import bpy,os
O=r"D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/gmw/"
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=O+"orig.glb")
m=bpy.data.materials.get('wall')
for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE':
        im=n.image;print("IMG",im.name,im.size[:]);im.filepath_raw=O+"img/"+im.name+".png";im.file_format='PNG';im.save()
import numpy as np
for o in bpy.data.objects:
    if o.type=='MESH' and any(s.material==m for s in o.material_slots):print("OBJ",o.name,o.dimensions[:])
bpy.ops.wm.save_as_mainfile(filepath=O+"g.blend")
