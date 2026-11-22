import bpy,bmesh,json,sys,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'))
IN=np.array([p[:2] for p in J['inner']]);IZ=J['iz'];oc=np.array(J['oc'][:2]);w=17
v=IN-oc;r=np.hypot(v[:,0],v[:,1]);u=v/r[:,None]
rs=np.convolve(np.r_[r[-w:],r,r[:w]],np.ones(w)/w,'same')[w:-w];INs=oc+u*rs[:,None];N=len(INs)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof8.glb')
me=bpy.data.objects['optus'].data;names=[m.name for m in me.materials];ie=names.index('roof_edge')
bm=bmesh.new();bm.from_mesh(me);uv=bm.loops.layers.uv.active
old=[f for f in bm.faces if f.material_index==ie];bmesh.ops.delete(bm,geom=old,context='FACES')
top=[bm.verts.new((x,y,IZ-0.02)) for x,y in INs];bot=[bm.verts.new((x,y,IZ-1.2)) for x,y in INs]
for i in range(N):
    j=(i+1)%N
    for q in((top[i],bot[i],bot[j],top[j]),):
        f=bm.faces.new(q);f.material_index=ie;f.smooth=False
        for l,(a,b) in zip(f.loops,((i/8,0),(i/8,1),((i+1)/8,1),((i+1)/8,0))):l[uv].uv=(a,b)
    # bottom lip 0.3 m inward toward the field
    pass
bm.normal_update();print('DEL',len(old),'NEW',N)
bm.to_mesh(me);bpy.ops.export_scene.gltf(filepath=D+'optus_roof9.glb',export_format='GLB')
