import bpy,bmesh,json,sys,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);IZ=J['iz'];ZF=46.55;ZS=44.4;N=len(RF)
oc=np.array(J['oc'][:2])
def smooth(R,w=17):
    v=R-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None];rs=np.convolve(np.r_[r[-w:],r,r[:w]],np.ones(w)/w,'same')[w:-w];return oc+u*rs[:,None]
RFs,INs=smooth(RF),smooth(IN);GL=np.array([p[:2] for p in J['glass']])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof3.glb')
o=bpy.data.objects['optus'];me=o.data;names=[m.name for m in me.materials];iw=names.index('white')
m=bpy.data.materials.new('soffit');m.use_nodes=True;nt=m.node_tree;t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(D+'soffit.png');t.image.pack()
nt.links.new(t.outputs[0],nt.nodes['Principled BSDF'].inputs['Base Color']);me.materials.append(m);isf=len(me.materials)-1
d=INs-RFs;L2=(d*d).sum(1)
def loc(x,y):
    q=np.array([x,y])-RFs;t=(q*d).sum(1)/L2;tc=np.clip(t,-0.2,1.2);e=((RFs+d*tc[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return t[i],e[i]
bm=bmesh.new();bm.from_mesh(me);uv=bm.loops.layers.uv.active
kill=[]
for f in bm.faces:
    if f.material_index!=iw:continue
    c=f.calc_center_median();t,e=loc(c.x,c.y)
    if e<16 and ((t>0.9 and c.z>IZ-1.2) or (t<0.03 and c.z>ZF+0.02)):kill.append(f)
bmesh.ops.delete(bm,geom=kill,context='FACES')
# soffit ring: glass top -> roof edge, just under ZS, facing down
z=ZS-0.03;A=[bm.verts.new((*GL[i],z)) for i in range(N)];B=[bm.verts.new((*RFs[i],z)) for i in range(N)]
s=0.0
for i in range(N):
    j=(i+1)%N;f=bm.faces.new((A[i],B[i],B[j],A[j]));f.material_index=isf
    L=np.linalg.norm(RFs[j]-RFs[i])
    for l in f.loops:
        k=[A[i],B[i],B[j],A[j]].index(l.vert);u=(s+(L if k in(2,3) else 0))/10;r=np.linalg.norm(np.array(l.vert.co[:2])-GL[i if k in(0,1) else j])
        l[uv].uv=(u,r/10)
    s+=L
    if f.normal.z>0:f.normal_flip()
bm.to_mesh(me);print('KILL',len(kill))
bpy.ops.export_scene.gltf(filepath=D+'optus_roof4.glb',export_format='GLB')
