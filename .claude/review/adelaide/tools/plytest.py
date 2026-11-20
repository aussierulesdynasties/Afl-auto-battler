import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=os.path.abspath('model/towers.ply'))
o=bpy.context.selected_objects[0]; me=o.data
print('UV', [u.name for u in me.uv_layers], 'COL', [(c.name,c.domain,c.data_type) for c in me.color_attributes])
c=me.color_attributes[0]; print('col0', tuple(c.data[0].color)); print('uv0', tuple(me.uv_layers[0].data[0].uv) if me.uv_layers else None)
