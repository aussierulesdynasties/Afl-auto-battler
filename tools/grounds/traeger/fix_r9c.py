import bpy,os
f=bpy.data.objects['green_roof_f'];u=bpy.data.objects['green_roof_f_u']
f.material_slots[0].material=bpy.data.materials['roof_green'];u.material_slots[0].material=bpy.data.materials['roof_soffit']
exec(open(r'C:/Users/DANTE/AppData/Local/Temp/claude/4a2d69a2e2816321/2e119eb6-c1b8-4f9d-a827-983cffaeebc1/scratchpad/pairfix.py').read())
print('FLIPPED',pair_fix(list(bpy.data.collections['model'].objects)))
for n in ('green_roof_f','green_roof_f_u','green_roof_b','green_roof_b_u'):
    o=bpy.data.objects[n];print('N',n,o.material_slots[0].material.name,round((o.matrix_world.to_3x3()@o.data.polygons[0].normal).z,2))
bpy.ops.wm.save_mainfile()
g=bpy.data.collections.get('ground')
for o in g.objects:o.select_set(False)
bpy.ops.export_scene.gltf(filepath=os.path.join(os.path.dirname(bpy.data.filepath),'traeger.glb'),export_format='GLB',export_cameras=False,export_lights=False);print('SAVED9')
