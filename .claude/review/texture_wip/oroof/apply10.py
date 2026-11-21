import bpy,bmesh,json,sys,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);IZ=J['iz'];ZF=46.55;oc=np.array(J['oc'][:2])
def sm(R,w=17):
    v=R-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None];rs=np.convolve(np.r_[r[-w:],r,r[:w]],np.ones(w)/w,'same')[w:-w];return oc+u*rs[:,None]
RF,IN=sm(RF),sm(IN);d=IN-RF;L2=(d*d).sum(1)
def loc(x,y):
    q=np.array([x,y])-RF;t=(q*d).sum(1)/L2;tc=np.clip(t,0,1);e=((RF+d*tc[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return t[i],e[i]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof9.glb')
me=bpy.data.objects['optus'].data;names=[m.name for m in me.materials];iw=names.index('white')
bm=bmesh.new();bm.from_mesh(me);n=0
for v in set(v for f in bm.faces if f.material_index==iw for v in f.verts):
    if not(40<v.co.z<52):continue
    t,e=loc(v.co.x,v.co.y)
    if -0.02<=t<=1.02 and e<4:
        zm=ZF+(IZ-ZF)*min(max(t,0),1)-0.08
        if v.co.z>zm:v.co.z=zm;n+=1
bm.to_mesh(me);print('CLAMP',n)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof10.glb',export_format='GLB')
