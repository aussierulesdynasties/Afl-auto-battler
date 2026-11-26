import json,numpy as np,trimesh
sc=trimesh.load('/home/user/Afl-auto-battler/assets/grounds/marvel/marvel.glb')
ms=[g for n,g in sc.geometry.items() if n.startswith(('tier','bowl'))]
M=trimesh.util.concatenate(ms);V=M.vertices;M=trimesh.Trimesh(np.c_[V[:,0],-V[:,2],V[:,1]],M.faces)
D=json.load(open('anal.json'));C=np.array([2.3151,0.6397]);U=np.array([0.33632,-0.94215]);Vv=np.array([-0.94215,-0.33632])
for nm in ['bN','bS']:
    A=np.array([p[3:] for p in D['P'] if p[0]==nm]);A=A[(A[:,2]>6.5)&(A[:,2]<38)]
    o=np.c_[A[:,:2],np.full(len(A),60.0)];dirs=np.tile([0,0,-1.0],(len(A),1))
    loc,ri,_=M.ray.intersects_location(o,dirs,multiple_hits=False)
    zt=np.full(len(A),np.nan);zt[ri]=loc[:,2]
    dz=A[:,2]-zt;u=(A[:,:2]-C)@U;v=(A[:,:2]-C)@Vv
    ok=~np.isnan(dz)&(np.abs(dz)<8)
    print(nm,'n',ok.sum(),'median dz (GE minus model seats below) %+.2f'%np.median(dz[ok]),'within1 %.0f%% within2 %.0f%%'%(np.mean(np.abs(dz[ok])<1)*100,np.mean(np.abs(dz[ok])<2)*100))
    for lo,hi in[(6,14),(14,22),(22,30),(30,38)]:
        m=ok&(A[:,2]>=lo)&(A[:,2]<hi)
        if m.sum():print('   z %d-%d n=%d med dz %+.2f |u| %.0f-%.0f'%(lo,hi,m.sum(),np.median(dz[m]),np.abs(u[m]).min(),np.abs(u[m]).max()))
    print('  section |v|<30: |u|, GE z, model z below')
    for k in np.argsort(np.abs(u)):
        if ok[k] and abs(v[k])<30: print('   %5.1f %5.1f %5.1f'%(abs(u[k]),A[k,2],zt[k]))
# model section at v=0
for uu in range(66,112,3):
    p=C+U*uu;loc,_,_=M.ray.intersects_location([[p[0],p[1],60]],[[0,0,-1]],multiple_hits=False)
    print('model u',uu,'z',loc[:,2].round(1) if len(loc) else None)
