import bpy,mathutils
for n in ['apron','fence','bowl']:
    o=bpy.data.objects[n]; print('MAT',n,[s.material.name if s.material else None for s in o.material_slots])
for o in bpy.data.objects:
    if o.type=='MESH' and 'pave' in ''.join(s.material.name for s in o.material_slots if s.material):
        me=o.data; inside=sum(1 for v in me.vertices if (o.matrix_world@v.co).xy.length<120)
        print('PAVE',o.name,len(me.vertices),'verts_inside120',inside)
