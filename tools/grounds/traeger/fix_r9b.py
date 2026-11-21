import bpy,sys
f=bpy.data.objects['green_roof_f'];u=bpy.data.objects['green_roof_f_u']
mf=f.material_slots[0].material;mu=u.material_slots[0].material
f.material_slots[0].material=mu;u.material_slots[0].material=mf
for o in (f,u):print('N',o.name,o.material_slots[0].material.name,[round(x,2) for x in (o.matrix_world.to_3x3()@o.data.polygons[0].normal)])
bpy.ops.wm.save_mainfile();print('SAVED9')
