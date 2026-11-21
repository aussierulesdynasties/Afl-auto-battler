# What ships: optus.glb + seats rebuilt from seat_tmpl.bin / seats_*.bin (glTF frame -> Blender), one colour per file
import bpy,sys,os,glob,numpy as np
a=sys.argv[sys.argv.index('--')+1:];glb,sd=a[0],a[1]
for o in list(bpy.data.objects):bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=glb)
COL={'seat_lo_blue':(0.616,0.624,0.683),'seat_lo_tan':(0.777,0.653,0.533),'seat_mid_blue':(0.832,0.714,0.602),'seat_mid_tan':(1.0,0.746,0.462),'seat_up_blue':(0.392,0.464,0.582),'seat_up_tan':(0.520,0.489,0.446)}
C=np.array([[1,0,0],[0,0,1],[0,-1,0.0]]);T=np.fromfile(os.path.join(sd,'seat_tmpl.bin'),'<f4').reshape(-1,3)
for f in sorted(glob.glob(os.path.join(sd,'seats_*.bin'))):
    X=np.fromfile(f,'<f4').reshape(-1,3,4);V=(np.einsum('nij,tj->nti',X[:,:,:3],T)+X[:,None,:,3]).reshape(-1,3)@C
    me=bpy.data.meshes.new(os.path.basename(f));me.from_pydata([tuple(v) for v in V],[],[(i,i+1,i+2) for i in range(0,len(V),3)]);me.update()
    ob=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(ob)
    name=os.path.basename(f)[6:-4];m=bpy.data.materials.get(name) or bpy.data.materials.new(name);me.materials.append(m);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*COL[name],1)
    print('SHIP',name,len(X))
bpy.ops.wm.save_as_mainfile(filepath=a[2])
