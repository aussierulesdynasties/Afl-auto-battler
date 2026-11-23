import bpy,sys,bmesh,collections
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
o=[o for o in bpy.data.objects if o.type=='MESH'][0];me=o.data
names=[s.material.name for s in o.material_slots]
bb=collections.defaultdict(lambda:[1e9,-1e9,1e9,-1e9,1e9,-1e9,0])
for p in me.polygons:
    n=names[p.material_index]
    if n not in('roof','roofd','roofg','fascia','under','soffit'):continue
    c=p.center;q=(n,int(c.x//40),int(c.y//40));b=bb[q]
    b[0]=min(b[0],c.x);b[1]=max(b[1],c.x);b[2]=min(b[2],c.y);b[3]=max(b[3],c.y);b[4]=min(b[4],c.z);b[5]=max(b[5],c.z);b[6]+=1
for k in sorted(bb):print(k,["%.0f"%v for v in bb[k][:6]],bb[k][6])
