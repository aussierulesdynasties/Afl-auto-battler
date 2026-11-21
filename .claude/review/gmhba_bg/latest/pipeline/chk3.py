import bpy, sys, numpy as np
bpy.ops.import_scene.gltf(filepath=sys.argv[-1])
o=bpy.data.objects['gmhba']; M=np.array(o.matrix_world)
V=np.array([v.co[:] for v in o.data.vertices]); V=V@M[:3,:3].T+M[:3,3]
H=V[V[:,2]>50]; cl=[]
for p in H:
    for c in cl:
        if np.hypot(*(c[0][:2]/c[1]-p[:2]))<15: c[0]+=p; c[1]+=1; c[2]=max(c[2],p[2]); c[3]=min(c[3],p[2]) ;break
    else: cl.append([p.copy(),1,p[2],p[2]])
for s,n,zt,zb in cl: print('TW',(s[:2]/n).round(1),n,round(zt,1))
