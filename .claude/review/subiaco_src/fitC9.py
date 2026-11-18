import numpy as np,json,math,sys
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if t=='t' and x<600],float)
GB=np.array([(x,y) for x,y,t in E if t=='b' and 300<x<690],float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15]
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126)])
RRI=np.array([(497,553),(576,525),(655,497),(734,459),(813,421),(892,396),(971,371)],float)
# towers: (top, foot) ; near tower foot hidden -> lean only
TWF=[((205,95),(212,250)),((512,15),(517,165)),((900,140),(914,370))]
TWN=((548,262),(556,485))
POSTS=np.array([(771.7,251),(788,253)],float)   # right-end goal post bases
def frame(q):
    th,dx,dy=q;a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)]);return U,V,np.array([dx,dy])
def ground(q):
    U,V,c=frame(q);ov=np.outer(PN[:,0]*92.65,U)+np.outer(PN[:,1]*64.15,V)+c;return np.vstack([ov,ov[:1]])
def res(p,F,full=False):
    cam=list(p[:6])+[F];q=p[6:9];h=p[9];ov=ground(q);O3=np.c_[ov,np.zeros(len(ov))]
    po=proj(cam,O3,cx,cy)
    r1=curve_d(GR,po)
    r3=curve_d(RRI,proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy))
    # near side: projected boundary must lie at/below the roof-occlusion edge (hidden)
    rb=[]
    for u,v in GB[::4]:
        m=np.abs(po[:,0]-u)<6
        if not m.any():rb.append(0.0);continue
        yy=po[m,1].max()
        rb.append(min(0.0,yy-v))
    rb=np.array(rb)
    U,V,c=frame(q);ends=[c+92.65*U,c-92.65*U];pe=[proj(cam,np.array([[*e,0]]),cx,cy)[0] for e in ends]
    e=ends[int(np.argmin([abs(x[0]-780) for x in pe]))];sgn=1
    pp=proj(cam,np.array([[*(e+3.2*V),0],[*(e-3.2*V),0]]),cx,cy);pp=pp[np.argsort(pp[:,0])]
    r5=(pp-POSTS).ravel()
    r4=[]
    for t,l in TWF:
        X=at_z(cam,*l,cx,cy,0.0);tp=proj(cam,np.array([X+[0,0,h]]),cx,cy)[0];r4+=list(tp-np.array(t))
    t,l=TWN;X=at_z(cam,*l,cx,cy,0.0);qq=proj(cam,np.array([X,X+[0,0,60]]),cx,cy);d=qq[1]-qq[0];d/=np.linalg.norm(d)
    v=np.array(t)-np.array(l);r4.append(d[0]*v[1]-d[1]*v[0]);r4=np.array(r4)
    if full:return r1,r3,rb,r5,r4
    return np.concatenate([r1,r3*2,rb,r5*2,r4*2])
out=[]
for F in [float(a) for a in sys.argv[1:]]:
  best=None
  for yaw0 in (40,50,60,70):
    for pit in (-25,-35,-45):
      D=F*250/700;pr=math.radians(pit);yw=math.radians(yaw0)
      C=[-D*math.cos(pr)*math.cos(yw),-D*math.cos(pr)*math.sin(yw),-D*math.sin(pr)]
      p0=C+[yw,pr,math.radians(-3),0,0,0,50]
      try:sol=least_squares(res,p0,args=(F,),loss='soft_l1',f_scale=2,max_nfev=600,x_scale='jac')
      except Exception as ex:continue
      sol=least_squares(res,sol.x,args=(F,),loss='linear',max_nfev=400,x_scale='jac')
      c=(sol.fun**2).mean()
      if best is None or c<best[0]:best=(c,sol.x)
  if best is None:print(F,'fail');continue
  r1,r3,rb,r5,r4=res(best[1],F,True);rm=lambda r:round(float(np.sqrt(np.median(np.square(r)))),2)
  p=best[1];print(F,'cost',round(best[0],2),'grass',rm(r1),'rr',rm(r3),'nearhinge',round(float(np.abs(rb).max()),1),'posts',np.round(r5,1),'tow',np.round(r4,1),'h',round(p[9],1),'ypr',np.round(np.degrees(p[3:6]),1),'dist',round(float(np.linalg.norm(p[:3]))),flush=True)
  out.append((best[0],F,list(p)))
out.sort();c,F,p=out[0]
json.dump({'p':p[:6]+[F,1.0],'W':W,'H':H,'groundC':list(p[6:9])+[1.0],'towh':p[9],'oval':ground(p[6:9]).tolist()},open('camC9.json','w'))
print('best',F)
