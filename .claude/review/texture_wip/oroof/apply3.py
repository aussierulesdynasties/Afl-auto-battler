import bpy,bmesh,json,sys,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);IZ=J['iz'];ZF=46.55;N=len(RF)
oc=np.array(J['oc'][:2])
def smooth(R,w=17):
    v=R-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None]
    k=np.ones(w)/w;rs=np.convolve(np.r_[r[-w:],r,r[:w]],k,'same')[w:-w];return oc+u*rs[:,None]
RFs,INs=smooth(RF),smooth(IN)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof2.glb')
o=bpy.data.objects['optus'];me=o.data;names=[m.name for m in me.materials];iw=names.index('white')
d=IN-RF;L2=(d*d).sum(1)
def loc(x,y):
    q=np.array([x,y])-RF;t=(q*d).sum(1)/L2;tc=np.clip(t,-0.2,1.2);e=((RF+d*tc[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return i,t[i],e[i]
bm=bmesh.new();bm.from_mesh(me)
kill=[]
for f in bm.faces:
    if f.material_index!=iw:continue
    c=f.calc_center_median();i,t,e=loc(c.x,c.y)
    if -0.05<t<1.05 and e<9 and c.z>ZF+(IZ-ZF)*min(max(t,0),1)+0.05 and c.z<52:kill.append(f)
bmesh.ops.delete(bm,geom=kill,context='FACES')
mv=0
for v in bm.verts:
    if not(40<v.co.z<50):continue
    i,t,e=loc(v.co.x,v.co.y)
    if e<1e-4 and -0.01<=t<=1.01:
        p=RFs[i]+(INs[i]-RFs[i])*t;v.co.x,v.co.y=p;mv+=1
bm.to_mesh(me);print('KILL',len(kill),'MOVED',mv)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof3.glb',export_format='GLB')
