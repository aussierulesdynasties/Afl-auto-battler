import bpy
bad = []
for m in bpy.data.materials:
    if m.node_tree:
        for n in m.node_tree.nodes:
            if (n.bl_idname.startswith('ShaderNodeTex') and n.bl_idname not in ('ShaderNodeTexImage','ShaderNodeTexCoord')) or n.bl_idname in ('ShaderNodeMapping','ShaderNodeBump'):
                bad.append((m.name, n.bl_idname))
print('PROCEDURAL', len(bad), bad[:50])
