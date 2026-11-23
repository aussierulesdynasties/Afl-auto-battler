import sys,numpy as np
from scipy.optimize import least_squares
from camsolve import *
LL=float(sys.argv[1]); TWR=sys.argv[4]; DMIN=float(sys.argv[2]); DMAX=float(sys.argv[3])
near=np.array([[0,1262],[250,1257],[500,1252],[700,1242],[900,1230],[1100,1218],[1300,1205],[1450,1192],[1600,1177],[1750,1165],[1900,1152]],float)
head=(1057,86); shaft=(1060,560)
posts=np.array([[1728,823],[1647,822],[1726,765],[1645,765]],float)
def res7(q):
    b=TW[TWR]; ht=proj(q,np.array([[b[0],b[1],65.0]]))[0][0]
    l0=proj(q,np.array([[b[0],b[1],0.0],[b[0],b[1],60.0]]))[0]; d=l0[1]-l0[0]; n=np.array([-d[1],d[0]])/np.linalg.norm(d)
    r3=(np.array(shaft)-l0[0])@n
    c=campos(q); a=np.linspace(0,360,7201)[:-1]; P=fpt(a,q[7]); uv,z=proj(q,P)
    dist=np.linalg.norm(P[:,:2]-c[:2],axis=1); m=(z>0)&(dist<60)
    u=uv[m,0];v=uv[m,1];o=np.argsort(u);u,v=u[o],v[o]
    if len(u)<5 or u.min()>0 or u.max()<1900: rn=np.full(len(near),300.0)
    else: rn=near[:,1]-np.interp(near[:,0],u,v)
    uvp,_=proj(q,np.array([[LL,-2.8,0],[LL,2.8,0],[LL,-2.8,3.0],[LL,2.8,3.0]]))
    return np.concatenate([ht-np.array(head),[r3],rn,(uvp-posts).ravel()])
best=None
for th0 in (250,260,270,280,290):
 for d0 in sorted(set([DMIN+0.01,(DMIN+DMAX)/2,DMAX-0.01])):
  for hc0 in (2,4,7):
    try: s=least_squares(res7,[th0,d0,hc0,77.5,1.1,-0.3,1968,1.0,0.0],bounds=([180,DMIN,0.5,0,-30,-10,600,0.5,-0.5],[360,DMAX,20,180,30,10,6000,2.5,0.5]))
    except Exception: continue
    if best is None or s.cost<best.cost: best=s
q=best.x; r=res7(q)
print(LL,np.round(q,2),'cost %.1f'%best.cost,'tower',np.round(r[:3],1),'near',np.round(r[3:14],1),'posts',np.round(r[14:],1),'cam',np.round(campos(q),2))
np.save('cam8n_%d_%s.npy'%(int(LL),TWR),q)
