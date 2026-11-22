import json,math,numpy as np,trimesh,sys
glb=sys.argv[1] if len(sys.argv)>1 else '/home/user/Afl-auto-battler/assets/grounds/optus/optus.glb'
F=360/math.tan(math.radians(25.58/2))
sc=trimesh.load(glb,force='scene');m=sc.to_geometry()
V=m.vertices.copy();m.vertices=np.stack([V[:,0],-V[:,2],V[:,1]],1)  # glTF (x,y up,z) -> model (x, y north, z up)
# ground plane at z=0 so rays that miss the stadium still land somewhere
g=trimesh.Trimesh([[-2000,-2000,0],[2000,-2000,0],[2000,2000,0],[-2000,2000,0]],[[0,1,2],[0,2,3]])
m=trimesh.util.concatenate([m,g])
I=trimesh.ray.ray_pyembree.RayMeshIntersector(m)
cams=json.load(open(sys.argv[2] if len(sys.argv)>2 else 'obl/cams.json'));P=json.load(open(sys.argv[3] if len(sys.argv)>3 else 'fac_pts.json'))
rows=[]
for nm,c in cams.items():
    C=np.array(c['cam']);z=np.array(c['tgt'])-C;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1.0]);x/=np.linalg.norm(x);y=np.cross(z,x)
    pts=[(k,v) for k,v in P.items() if v and k.startswith(nm+'_')]
    if not pts:continue
    D=np.array([((v[0]-640)/F)*x+((v[1]-360)/F)*y+z for k,v in pts]);D/=np.linalg.norm(D,axis=1)[:,None]
    loc,ir,_=I.intersects_location(np.repeat(C[None],len(D),0),D,multiple_hits=False)
    hit={int(i):l for i,l in zip(ir,loc)}
    for j,(k,v) in enumerate(pts):
        G=np.array(v[2:5]);
        if j not in hit:continue
        H=hit[j];rows.append([int(nm[1:]),np.linalg.norm(G-C),np.linalg.norm(H-C),*G,*H])
R=np.array(rows);np.save(sys.argv[4] if len(sys.argv)>4 else 'obl/rayck.npy',R)
dd=R[:,2]-R[:,1];e3=np.linalg.norm(R[:,6:9]-R[:,3:6],axis=1)
print('n',len(R),'depth ours-GE: med %.2f  |med| %.2f  p75 %.2f'%(np.median(dd),np.median(abs(dd)),np.percentile(abs(dd),75)))
for lo,hi in [(-2,3),(3,9),(9,15),(15,25),(25,35),(35,45)]:
    mm=(R[:,5]>=lo)&(R[:,5]<hi);print('h %2d-%2d n %3d depth med %.2f |med| %.2f   3D |med| %.2f'%(lo,hi,mm.sum(),np.median(dd[mm]),np.median(abs(dd[mm])),np.median(e3[mm])))
for vw in sorted(set(R[:,0])):
    mm=R[:,0]==vw;print('view %3d n %2d |depth| med %.2f p75 %.2f'%(vw,mm.sum(),np.median(abs(dd[mm])),np.percentile(abs(dd[mm]),75)))
