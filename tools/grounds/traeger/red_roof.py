import bpy
sc=bpy.context.scene;print('ENGINE',sc.render.engine)
m=bpy.data.materials['roof_green'];nt=m.node_tree;b=nt.nodes['Principled BSDF']
for l in list(b.inputs['Base Color'].links):print('LINK',l.from_node.type);nt.links.remove(l)
b.inputs['Base Color'].default_value=(1,0,0,1)
b.inputs['Specular IOR Level'].default_value=0.0;b.inputs['Roughness'].default_value=1.0
