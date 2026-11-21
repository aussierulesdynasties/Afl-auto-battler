import bpy,sys,numpy as np
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=a[0])
P=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    M=o.matrix_world
    for v in o.data.vertices:
        w=M@v.co;P.append((w.x,-w.z,w.y) if False else (w.x,w.y,w.z))
P=np.array(P)
# glTF import: blender z up already
for c in [(-122.5,-52.6),(-51.9,107.9)]:
    d=np.hypot(P[:,0]-c[0],P[:,1]-c[1]);m=(d<9)
    S=P[m];lo=S[S[:,2]<0.3];hi=S[S[:,2]>74]
    print(c,'base ctr',lo[:,:2].mean(0).round(2) if len(lo) else None,'n',len(lo),'top ctr',hi[:,:2].mean(0).round(2), 'zmax',S[:,2].max().round(2))
