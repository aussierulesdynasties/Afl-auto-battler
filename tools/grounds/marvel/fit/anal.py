import sys,json,math,numpy as np,trimesh
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/marvel')
import surrounds as S
sc=trimesh.load('/home/user/Afl-auto-battler/assets/grounds/marvel/marvel.glb')
ms=[g for n,g in sc.geometry.items() if not n.startswith('roofshut')]
M=trimesh.util.concatenate(ms)
V=M.vertices.copy();M=trimesh.Trimesh(np.c_[V[:,0],-V[:,2],V[:,1]],M.faces)  # -> e,n,z
C=np.array([2.3151,0.6397]);U=np.array([0.33632,-0.94215]);Vv=np.array([-0.94215,-0.33632])
pq=trimesh.proximity.ProximityQuery(M)
def load(names):
    P=[]
    for nm in names:
        d=json.load(open(f'/tmp/claude-0/obl/{nm}/picks.json'))
        for k,v in d.items():
            if v is None:continue
            lat,lon,el=v[:3];e,n=S.xy(lat,lon);P.append((nm,*map(int,k.split(',')),e,n,el-2.6))
    return P
if __name__=='__main__':
    P=load(sys.argv[1:]);A=np.array([p[3:] for p in P])
    cp,dist,tri=pq.on_surface(A)
    uv=np.c_[(A[:,:2]-C)@U,(A[:,:2]-C)@Vv]
    json.dump(dict(P=P,cp=cp.tolist(),dist=dist.tolist()),open('/tmp/claude-0/obl/anal.json','w'))
    # facade picks: 3..30 m above street (street ~ z 8.4), not roof
    for nm in sorted(set(p[0] for p in P)):
        idx=np.array([i for i,p in enumerate(P) if p[0]==nm])
        z=A[idx,2];d=dist[idx]
        print(nm,len(idx),'within 1/2/5 m of model:',[round(float(np.mean(d<t))*100) for t in(1,2,5)],'median',round(float(np.median(d)),2))
