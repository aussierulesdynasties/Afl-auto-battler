import numpy as np,json,math
exec(open('fitA11.py').read().split('best=None\nfor f0')[0])
ext=PN[:,0].max();print('ext',ext,'min',PN[:,0].min())
GSE=np.array([(891,341),(926,343),(929,359),(891,358)],float)   # east goal square: field-side top, goal-line top, goal-line bottom, field-side bottom
GSW=np.array([(330,303),(294,303),(296,319),(330,319)],float)
POLE=(np.array([924,554.]),np.array([941,470.]))
def frame(p):
    th,dx,dy=p[7:10];a=a0+th;return np.array([math.cos(a),math.sin(a)]),np.array([-math.sin(a),math.cos(a)]),np.array([dx,dy])
def mdl(p):
    U,V,c=frame(p);L,B=p[10],p[11];A=L/ext
    ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*B,V)+c;ov=np.vstack([ov,ov[:1]])
    sq=np.outer(np.array([1,1,-1,-1,1])*25,U)+np.outer(np.array([1,-1,-1,1,1])*25,V)+c
    arcs=[];gs=[]
    for s in(1,-1):
        g=c+s*L*U;pts=g+50*np.c_[np.cos(t),np.sin(t)];rel=pts-c;e=(rel@U/A)**2+(rel@V/B)**2
        tt=np.mod(t-math.atan2(-s*U[1],-s*U[0])+np.pi,2*np.pi)-np.pi;sel=e<0.97;pts=pts[sel];arcs.append(pts[np.argsort(tt[sel])])
        gs.append(np.array([g-s*9*U+3.2*V*0+V*3.2*1,g+V*3.2,g-V*3.2,g-s*9*U-V*3.2]))
    return ov,sq,arcs,gs
def P(p,X):
    X=np.atleast_2d(X)
    if X.shape[1]==2:X=np.c_[X,np.zeros(len(X))]
    return projd(p[:7],X,cx,cy,p[12],p[13])
def curves(p):
    ov,sq,arcs,gs=mdl(p);return [ov,sq]+arcs
def assign(p,tol):
    C=curves(p);D=np.array([curve_d(LP,P(p,c)) if len(c)>1 else np.full(len(LP),1e3) for c in C]);k=D.argmin(0);dm=D.min(0)
    return [LP[(k==i)&(dm<tol)] for i in range(len(C))]
def sqres(q,I):
    best=None
    for k in range(4):
        d=(q[[(i+k)%4 for i in range(4)]]-I).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    return best
def res(p,G,full=False):
    ov,sq,arcs,gs=mdl(p);C=[ov,sq]+arcs
    r=[curve_d(g,P(p,c)) for g,c in zip(G,C) if len(g)]
    U,V,c=frame(p)
    rs=sqres(P(p,np.outer(np.array([1,1,-1,-1])*25,U)+np.outer(np.array([1,-1,-1,1])*25,V)+c),SQI)
    # goal squares: east is the +U or -U end, pick by image x
    q1=P(p,gs[0]);q2=P(p,gs[1])
    if q1[:,0].mean()<q2[:,0].mean():q1,q2=q2,q1
    rg=np.concatenate([sqres(q1,GSE),sqres(q2,GSW)])
    rr=curve_d(RRI,P(p,RR))
    b=POLE[0];X=None
    # pole: direction of projected vertical at the pole base vs photo
    cam=p[:7];bw=at_z(cam,*b,cx,cy,2);q=P(p,np.array([bw,bw+[0,0,30]]));dv=q[1]-q[0];dv/=np.linalg.norm(dv);dp=POLE[1]-POLE[0];dp/=np.linalg.norm(dp)
    rp=np.array([(dv[0]*dp[1]-dv[1]*dp[0])*80])
    out=(r,rs,rg,rr,rp)
    return out if full else np.concatenate(r+[rs*3,rg*0,rr*3,rp,[p[8]*0.3,p[9]*0.3]])
p0=np.array(json.load(open('pA13.json')));p=np.r_[p0[:10],p0[10]*ext,p0[11],0,0]
for kfree in (False,):
  for tol in (12,8,6,5):
    G=assign(p,tol)
    if kfree:sol=least_squares(lambda q:res(q,G),p,loss='soft_l1',f_scale=2)
    else:sol=least_squares(lambda q:res(np.r_[q,0,0],G),p[:12],loss='soft_l1',f_scale=2)
    p=sol.x if kfree else np.r_[sol.x,0,0]
    r,rs,rg,rr,rp=res(p,G,True);R=lambda x:round(float(np.sqrt(np.mean(np.square(x)))),2)
    print('k' if kfree else '-',tol,'n',[len(g) for g in G],'curves',[R(x) for x in r],'sq',R(rs),'gs',R(rg),'rr',R(rr),'pole',R(rp/80*57.3),'deg f',round(p[6]),'L B',np.round(p[10:12],1),'k',np.round(p[12:14],3),flush=True)
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1),'ground',np.round([math.degrees(p[7]),*p[8:12]],2))
json.dump(list(p),open('pA14k0.json','w'))

import subprocess
