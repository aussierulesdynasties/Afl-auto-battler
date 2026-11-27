import numpy as np, json
from scipy.optimize import least_squares
from ptsolve import *
C=json.load(open('/home/user/Afl-auto-battler/tools/grounds/legacy/subiaco/measure/fence_fit.json'))['c']
def fr(a):
    t=np.radians(a);v=C[0]+0*t
    for k in range(1,11): v=v+C[2*k-1]*np.cos(k*t)+C[2*k]*np.sin(k*t)
    return v
A=np.linspace(0,360,7201)[:-1]; R=fr(A); FP=np.stack([R*np.cos(np.radians(A)),R*np.sin(np.radians(A)),0*A],-1)
far=np.load('fa_far.npy')
obs={'bA':(1286.5,1092.5),'gA':(1495,1010),'gB':(1665,942.5),'bB':(1810,885),'sqA':(1170,917.5),'sqB':(1345,864)}
P3=goal('E',0); keys=list(obs); Aobs=np.array([obs[k] for k in keys],float); B=np.array([P3[k] for k in keys])
SE=px2m(1136.2,733.0); TL=np.array([[783,10],[783,150]],float)
def res(q,wf=1.0):
    uv,_=proj(q,B); r1=(uv-Aobs).ravel()
    uvf,z=proj(q,FP); d=np.linalg.norm(FP[:,:2]-q[:2],axis=1); m=(z>0)&(d>70)
    u=uvf[m,0];v=uvf[m,1];o=np.argsort(u);u,v=u[o],v[o]
    if len(u)<10 or u.min()>far[:,0].min() or u.max()<far[:,0].max(): r2=np.full(len(far),200.0)
    else: r2=(far[:,1]-np.interp(far[:,0],u,v))*wf
    l0,_=proj(q,np.array([[SE[0],SE[1],20.0],[SE[0],SE[1],60.0]])); dd=l0[1]-l0[0]; n=np.array([-dd[1],dd[0]])/np.linalg.norm(dd)
    r3=(TL-l0[0])@n
    return np.concatenate([r1,r2/np.sqrt(len(far)/10),r3])
q0=np.array([1.12140e+02,-3.56300e+01,1.48300e+01,1.40780e+02,-1.18000e+01,-1.13000e+00,2.14475e+03,0])
best=None
for F0 in (1700,2145,2700):
  for k0 in (-0.1,0,0.1):
    q=q0.copy(); q[6]=F0; q[7]=k0
    s=least_squares(res,q,bounds=([-300,-300,0.5,-1e3,-80,-20,500,-0.4],[300,300,80,1e3,40,20,8000,0.4]))
    if best is None or s.cost<best.cost: best=s
q=best.x; r=res(q); nb=12; nf=len(far)
print(np.round(q,3)); print('goal rms',np.sqrt((r[:nb]**2).mean()),'far rms',np.sqrt(((r[nb:nb+nf]*np.sqrt(nf/10))**2).mean()),'tower',r[-2:])
np.save('cam_fa_E2.npy',q)
f,rr,uu=Rm(*q[3:6])
def hit(uv,Y):
    x0=(uv[0]-W_/2)/q[6]; y0=-(uv[1]-H_/2)/q[6]
    # undo distortion approx (iterate)
    x,y=x0,y0
    for _ in range(10): s=1+q[7]*(x*x+y*y)*(q[6]/1200)**2; x,y=x0/s,y0/s
    d=f+x*rr+y*uu; t=(Y-q[1])/d[1]; return q[:3]+t*d
import cv2
g=cv2.imread('/home/user/work/subi/refs/commons/Foot_australien.JPG').astype(float).mean(2)
Yr=(1021-750)*0.2945
for x in range(1300,1900,100):
    col=g[120:220,x]; d=np.diff(col); i=int(np.argmin(d)); y=120+i+0.5
    p=hit((x,y),Yr); print(x,y,'roof top h %.1f X %.1f'%(p[2],p[0]))
