import json,numpy as np,sys
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
nB={};exec(open('w/fitPA6.py').read().split(chr(10)+'q5=json')[0],nB)
exec(open('w/cam.py').read())
D2,Nn,E,HZ,FB,OD=nB['D2'],nB['Nn'],np.array(nB['E']),np.array(nB['HZ'],float),np.array(nB['FB'],float),nB['OD']
W,H=757.,636.
G=json.load(open('w/geomA5.json'));s=G['pratt']
MT=np.array([np.array(s['back'][k])+[0,0,s['masth']] for k in s['mastidx']])
def dens(L,n=200):
    L=np.array(L);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(L,axis=0),axis=1))];t=np.linspace(0,d[-1],n)
    return np.stack([np.interp(t,d,L[:,i]) for i in range(L.shape[1])],1)
PF,PB=dens(s['front']),dens(s['back'])
tr=json.load(open('w/trB.json'))['pratt'];TF=dens(tr['front'])/3;TB=dens(tr['back'])/3
uM=np.array([(838,916),(870,913),(903,907),(934,901),(966,891),(997,883),(1030,870),(1063,860),(1098,845),(1138,837),(1183,832),(1228,835),(1273,842),(1318,850)],float)/3
WP=float(sys.argv[1]) if len(sys.argv)>1 else 1.0
def P(q,X):
    k=mk(q[:9]);u=k.proj(X);c=np.array([q[7],q[8]]);d=(u-c)/W;r2=(d**2).sum(1,keepdims=True)
    return c+d*W*(1+q[10]*r2+q[11]*r2*r2)
def undist(q,uv):
    c=np.array([q[7],q[8]]);d0=(uv-c)/W;d=d0.copy()
    for _ in range(8):
        r2=(d**2).sum(1,keepdims=True);d=d0/(1+q[10]*r2+q[11]*r2*r2)
    return c+d*W
def parts(q):
    k=mk(q[:9]);off=q[9]
    P2=P(q,np.c_[D2+Nn*off,np.zeros(len(D2))])
    r_edge=np.r_[cKDTree(P2).query(E)[0],cKDTree(E).query(P2)[0]*0.3]
    r_hz=[];M=k.M
    for u,v in undist(q,HZ):
        w=k.ray(u,v);r_hz.append(w[2]*q[6]*3)
    t=cKDTree(OD);r_fb=[]
    for u,v in undist(q,FB):
        X0=k.at_z(u,v,0);r_fb.append(t.query(X0[:2])[0]*3)
    r_m=(P(q,MT)-uM).ravel()
    pf=P(q,PF);pb=P(q,PB)
    r_c=np.r_[cKDTree(pf).query(TF)[0],cKDTree(TF).query(pf)[0],cKDTree(pb).query(TB)[0],cKDTree(TB).query(pb)[0]]
    return r_edge,np.array(r_hz),np.array(r_fb),r_m,r_c
def f(q):
    a,b,c,d,e=parts(q);return np.r_[a,b,c,d*WP,e*WP*0.3]
jb=json.load(open('w/camPA6.json'));q0=np.r_[jb['q'],jb['off'],0,0]
lo=[-np.inf]*6+[200,0,0,0,-1,-1];hi=[np.inf]*6+[3000,W,H,22,1,1]
best=None
for k1 in (0,-0.2,0.2):
    o=least_squares(f,np.r_[q0[:10],k1,0],loss='soft_l1',f_scale=2,max_nfev=4000,bounds=(lo,hi))
    if best is None or o.cost<best.cost:best=o
q=best.x
def rep(q,t):
    a,b,c,d,e=parts(q);n=len(E)
    print(t,'grass edge rms px(2271)',round(float(np.sqrt(np.mean(a[:n]**2)))*3,1),'horizon px',np.round(np.abs(b)/3*3,1).tolist(),'Legends base m',np.round(np.array(c)/3,1).tolist())
    print('   Pratt masts px(2271)',np.round(np.linalg.norm(d.reshape(-1,2),axis=1)*3).astype(int).tolist(),'Pratt roof edges rms px(2271)',round(float(np.sqrt(np.mean(e**2)))*3,1))
rep(np.r_[q0[:10],0,0],'old');rep(q,'new');print('k1 k2',np.round(q[10:],3),'C',np.round(q[:3],1),'off',round(q[9],2))
json.dump({'q':q[:9].tolist(),'off':q[9],'k':q[10:].tolist()},open('w/camPA8.json','w'))
