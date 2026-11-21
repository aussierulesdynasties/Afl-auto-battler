import bpy,bmesh
for n in ('green_roof_f','green_roof_b'):
    o=bpy.data.objects[n];me=o.data;print('N_BEFORE',n,[tuple(round(x,2) for x in (o.matrix_world.to_3x3()@p.normal)) for p in me.polygons])
o=bpy.data.objects['green_roof_f'];bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
