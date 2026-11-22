import bpy,bmesh,json,sys,numpy as np,math,collections
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);oc=np.array(J['oc'][:2])
def smooth(R,w=17):
    v=R-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None]
    k=np.ones(w)/w;rs=np.convolve(np.r_[r[-w:],r,r[:w]],k,'same')[w:-w];return rs,np.arctan2(v[:,1],v[:,0])
rs,ang=smooth(RF);o=np.argsort(ang);ang,rs=ang[o],rs[o]
def rad(a):return np.interp(a,ang,rs,period=2*math.pi)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof8.glb')
C=collections.Counter();A=collections.defaultdict(list)
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    me=ob.data;mw=ob.matrix_world
    for p in me.polygons:
        c=mw@p.center
        if c.z<38:continue
        a=math.atan2(c.y-oc[1],c.x-oc[0]);r=math.hypot(c.x-oc[0],c.y-oc[1])
        if r>rad(a)+0.15:
            k=(ob.name,me.materials[p.material_index].name if me.materials else '-');C[k]+=1;A[k].append(round(math.degrees(a)))
for k,v in C.most_common():print(k,v,sorted(set(A[k]))[:40])
