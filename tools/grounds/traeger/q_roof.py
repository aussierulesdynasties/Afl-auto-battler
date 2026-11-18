import bpy
m=bpy.data.materials.get('roof_green');print('MAT',m)
if m:
    for n in m.node_tree.nodes:
        print('NODE',n.type,getattr(getattr(n,'image',None),'filepath',''))
sc=bpy.context.scene;print('VIEW',sc.view_settings.view_transform,sc.view_settings.look,sc.view_settings.exposure)
for o in bpy.data.objects:
    if o.type=='LIGHT':print('LIGHT',o.name,o.data.type,o.data.energy)
w=sc.world
if w and w.node_tree:
    for n in w.node_tree.nodes:
        if n.type=='BACKGROUND':print('WORLD',n.inputs[1].default_value)
for o in bpy.data.objects:
    if o.type=='MESH' and any(s.material and s.material.name.startswith('roof_green') for s in o.material_slots):print('OBJ',o.name)
