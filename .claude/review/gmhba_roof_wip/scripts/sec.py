import bpy,sys,math,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
o=[o for o in bpy.data.objects if o.type=='MESH'][0];me=o.data;M=o.matrix_world
names=[s.material.name for s in o.material_slots]
B=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,1e9,-1e9,1e9,-1e9]))
for p in me.polygons:
    n=names[p.material_index];c=M@p.center;a=math.degrees(math.atan2(c.y,c.x));r=math.hypot(c.x,c.y)
    if not(100<a<200 or a<-170):continue
    if a<0:a+=360
    b=B[int(a//4)*4][n];b[0]+=1;b[1]=min(b[1],c.z);b[2]=max(b[2],c.z);b[3]=min(b[3],r);b[4]=max(b[4],r)
for k in sorted(B):
    print(k,' '.join("%s:%d z%.0f-%.0f r%.0f-%.0f"%(n,*v) for n,v in sorted(B[k].items()) if n in('roof','roofd','roofg','fascia','under','soffit','wall','glass','sign','beige','cream','navy')))
