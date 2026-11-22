import bpy,bmesh,json,sys,math,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'));oc=np.array(J['oc'][:2])
GL=np.array([p[:2] for p in J['glass']]);IN=np.array([p[:2] for p in J['inner']]);RF=np.array([p[:2] for p in J['roof']])
ga=np.arctan2(GL[:,1]-oc[1],GL[:,0]-oc[0]);gr=np.hypot(GL[:,0]-oc[0],GL[:,1]-oc[1]);o_=np.argsort(ga)
def rgl(a):return np.interp(a,ga[o_],gr[o_],period=2*math.pi)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof4.glb')
tot={}
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    me=ob.data;names=[m.name for m in me.materials];bm=bmesh.new();bm.from_mesh(me);kill=[]
    for f in bm.faces:
        n=names[f.material_index] if names else ''
        c=f.calc_center_median();a=math.atan2(c.y-oc[1],c.x-oc[0]);r=math.hypot(c.x-oc[0],c.y-oc[1])
        if n in('seats','aisle','aisle_step','riser','bench') and c.z>30 and r>rgl(a)-0.3:kill.append(f)
        if n=='roof_edge':
            # keep only the inner ring wall: within 0.6 m of the inner ring radius
            ia=np.arctan2(IN[:,1]-oc[1],IN[:,0]-oc[0]);ir=np.hypot(IN[:,0]-oc[0],IN[:,1]-oc[1]);oi=np.argsort(ia)
            if abs(r-np.interp(a,ia[oi],ir[oi],period=2*math.pi))>0.8:kill.append(f)
    bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(me);tot[ob.name]=len(kill)
print('KILL',tot)
bpy.ops.export_scene.gltf(filepath=D+'optus_roof5.glb',export_format='GLB')
