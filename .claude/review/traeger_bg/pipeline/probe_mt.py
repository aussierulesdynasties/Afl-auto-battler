import bpy, numpy as np
for o in bpy.data.objects:
    if o.name.startswith(('bg_roof','bg_bld_tower','bg_court_slab')):
        me=o.data; m=me.materials[0]
        print(o.name, m.name, [n.bl_idname for n in m.node_tree.nodes], [ (a.name,a.domain,a.data_type) for a in me.color_attributes], me.color_attributes.active_color_name)
        ca=me.color_attributes.get('Col'); c=np.zeros(len(ca.data)*4); ca.data.foreach_get('color',c); print('  col mean', c.reshape(-1,4).mean(0))
        for n in m.node_tree.nodes:
            if n.bl_idname=='ShaderNodeTexImage': print('  img', n.image.name, n.image.size[:], n.image.has_data)
            if n.bl_idname=='ShaderNodeVertexColor': print('  vc layer', n.layer_name)
