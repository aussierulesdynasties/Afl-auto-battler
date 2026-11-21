import bpy,bmesh,json,sys,math,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'));F=json.load(open(D+'ringfix.json'))
RF=np.array([p[:2] for p in J['roof']]);IN=np.array([p[:2] for p in J['inner']]);oc=np.array(J['oc'][:2])
def sm(R,w=17):
    v=R-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None];rs=np.convolve(np.r_[r[-w:],r,r[:w]],np.ones(w)/w,'same')[w:-w];return oc+u*rs[:,None]
RF,IN=sm(RF),sm(IN);d=IN-RF;L2=(d*d).sum(1);A=np.arange(0,360,2)
eo=lambda a:np.interp(a,A,F['outer'],period=360);ei=lambda a:np.interp(a,A,F['inner'],period=360)
def tpar(x,y):
    q=np.array([x,y])-RF;t=(q*d).sum(1)/L2;tc=np.clip(t,0,1);e=((RF+d*tc[:,None]-[x,y])**2).sum(1);i=int(e.argmin());return t[i]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof10.glb')
n=0
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data);mw=ob.matrix_world
    for v in bm.verts:
        w=mw@v.co
        if w.z<38:continue
        x,y=w.x-oc[0],w.y-oc[1];r=math.hypot(x,y);a=math.degrees(math.atan2(y,x))%360
        t=min(max(tpar(w.x,w.y),0),1);dr=-(eo(a)*(1-t)+ei(a)*t)
        if w.z<40:dr*=(w.z-38)/2   # fade in under the roof so columns don't tear
        if dr==0:continue
        nw=w.copy();nw.x=oc[0]+x*(r+dr)/r;nw.y=oc[1]+y*(r+dr)/r;v.co=mw.inverted()@nw;n+=1
    bm.to_mesh(ob.data)
print('MOVED',n)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof11.glb',export_format='GLB')
