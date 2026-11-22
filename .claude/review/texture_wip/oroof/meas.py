import bpy,sys,math,json,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'));oc=J['oc']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof4.glb')
me=bpy.data.objects['optus'].data;names=[m.name for m in me.materials]
st={}
for p in me.polygons:
    n=names[p.material_index]
    if n not in('glass','seats','soffit','under','white'):continue
    c=p.center;a=math.degrees(math.atan2(c.y-oc[1],c.x-oc[0]))
    if -75<a<-65:
        r=math.hypot(c.x-oc[0],c.y-oc[1]);st.setdefault(n,[]).append((round(r,1),round(c.z,1)))
for n,v in st.items():
    v=np.array(v);print(n,len(v),'r',v[:,0].min(),v[:,0].max(),'z',v[:,1].min(),v[:,1].max())
    if n=='seats':
        top=v[v[:,1]>40];print(' seats>40m r',top[:,0].min() if len(top) else None,top[:,0].max() if len(top) else None)
    if n=='glass':print(' glass top z at r>',v[v[:,1]>40][:,0].min() if (v[:,1]>40).any() else None)
