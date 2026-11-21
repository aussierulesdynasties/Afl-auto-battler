import bpy
m = bpy.data.materials['lm_veil']
print('VEIL', m.surface_render_method, getattr(m,'blend_method',None))
for n in m.node_tree.nodes: print('VEIL node', n.bl_idname, n.name, getattr(n,'image',None) and n.image.name, getattr(n,'interpolation',None))
for l in m.node_tree.links: print('VEIL link', l.from_node.name, l.from_socket.name, '->', l.to_node.name, l.to_socket.name)
