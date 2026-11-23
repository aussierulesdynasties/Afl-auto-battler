import bpy
o=bpy.data.objects['gmhba']
for s in o.material_slots:
  m=s.material
  if m and m.name=='wall':
    for n in m.node_tree.nodes:
      if n.type=='TEX_IMAGE': print('WALLIMG',n.image.name,n.image.size[:],n.image.filepath)
