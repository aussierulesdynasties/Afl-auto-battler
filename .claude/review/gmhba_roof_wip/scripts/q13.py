import bpy,sys,math,collections
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
d=collections.defaultdict(lambda:-1e9)
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    me=o.data;M=o.matrix_world
    for p in me.polygons:
        n=me.materials[p.material_index].name
        if n not in('seatback','seatpan','tread'):continue
        v=M@p.center;an=math.degrees(math.atan2(v.y,v.x))%360;r=math.hypot(v.x,v.y)
        if 120<an<160 and 74<r<100:
            k=(int(an//2)*2,int(r//2)*2);d[k]=max(d[k],v.z)
for r in range(74,100,2):print('R',r,' '.join('%5.1f'%d[(a_,r)] if d[(a_,r)]>-1e8 else '  -  ' for a_ in range(120,160,2)))
