import bpy,bmesh,json,sys,numpy as np,math
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
RF=np.array([p[:2] for p in J['roof']]);oc=np.array(J['oc'][:2])
v=RF-oc;r0=np.hypot(v[:,0],v[:,1]);ang=np.arctan2(v[:,1],v[:,0]);w=17
rs=np.convolve(np.r_[r0[-w:],r0,r0[:w]],np.ones(w)/w,'same')[w:-w]
o=np.argsort(ang);ang,r0,rs=ang[o],r0[o],rs[o]
R0=lambda a:np.interp(a,ang,r0,period=2*math.pi);RS=lambda a:np.interp(a,ang,rs,period=2*math.pi)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof7.glb')
me=bpy.data.objects['optus'].data;names=[m.name for m in me.materials]
bm=bmesh.new();bm.from_mesh(me);rb=names.index('roof_bay')
skip=set(v for f in bm.faces if f.material_index==rb for v in f.verts)
sh=cl=0
for vt in bm.verts:
    if vt in skip or not(38<vt.co.z<50):continue
    x,y=vt.co.x-oc[0],vt.co.y-oc[1];a=math.atan2(y,x);r=math.hypot(x,y);r2=r
    if r>R0(a)-6:r2=r+(RS(a)-R0(a));sh+=1
    if r2>RS(a)-0.05:r2=RS(a)-0.05;cl+=1
    if r2!=r:vt.co.x=oc[0]+x*r2/r;vt.co.y=oc[1]+y*r2/r
bm.to_mesh(me);print('SHIFT',sh,'CLAMP',cl)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof8.glb',export_format='GLB')
