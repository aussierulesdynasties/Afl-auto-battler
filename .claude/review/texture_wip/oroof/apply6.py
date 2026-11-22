import bpy,bmesh,json,sys,math,numpy as np
D=sys.argv[-1];J=json.load(open(D+'../obuild/geom.json'));oc=np.array(J['oc'][:2]);IZ=J['iz']
IN=np.array([p[:2] for p in J['inner']]);ia=np.arctan2(IN[:,1]-oc[1],IN[:,0]-oc[0]);ir=np.hypot(IN[:,0]-oc[0],IN[:,1]-oc[1]);oi=np.argsort(ia)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=D+'optus_roof5.glb')
ob=bpy.data.objects['optus'];me=ob.data;names=[m.name for m in me.materials];bm=bmesh.new();bm.from_mesh(me);kill=[]
for f in bm.faces:
    if names[f.material_index]!='white':continue
    c=f.calc_center_median();a=math.atan2(c.y-oc[1],c.x-oc[0]);r=math.hypot(c.x-oc[0],c.y-oc[1])
    if abs(r-np.interp(a,ia[oi],ir[oi],period=2*math.pi))<2.5 and c.z>IZ-1.5:kill.append(f)
bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(me);print('KILL',len(kill))
bpy.ops.export_scene.gltf(filepath=D+'optus_roof6.glb',export_format='GLB')
