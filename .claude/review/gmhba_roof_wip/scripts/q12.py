import bpy,sys,math,collections
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
c=collections.Counter();z=collections.defaultdict(lambda:[1e9,-1e9,1e9,-1e9])
for o in bpy.context.scene.objects:
    if o.type!='MESH':continue
    me=o.data;M=o.matrix_world
    for p in me.polygons:
        v=M@p.center
        if v.x<-100 and -10<v.y<45 and v.z>12:
            n=me.materials[p.material_index].name if me.materials else '-';c[(o.name,n)]+=1
            r=z[(o.name,n)];r[0]=min(r[0],v.y);r[1]=max(r[1],v.y);r[2]=min(r[2],v.z);r[3]=max(r[3],v.z)
for k,v in c.most_common(30):print('Q',k,v,[round(x,1) for x in z[k]])
