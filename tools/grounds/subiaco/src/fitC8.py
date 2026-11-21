import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if t=='t'],float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15]
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126)])
RRI=np.array([(497,553),(576,525),(655,497),(734,459),(813,421),(892,396),(971,371)],float)
TW=[((554.1,300),(563.1,465)),((914.3,180),(916.0,343)),((201.2,130),(213.0,252.5)),((510.2,40),(517.3,160))]
def ground(q):
    th,dx,dy,s=q;a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)])
    ov=np.outer(PN[:,0]*92.65*s,U)+np.outer(PN[:,1]*64.15*s,V)+[dx,dy];return np.vstack([ov,ov[:1]])
def vp(cam):
    M=R(*cam[3:6]);d=M@np.array([0,0,-1.0]);return np.array([cx+cam[6]*d[0]/d[2],cy-cam[6]*d[1]/d[2]]) if abs(d[2])>1e-9 else None
def res(p,F,full=False):
    cam=list(p[:6])+[F];ov=ground(p[6:10])
    r1=curve_d(GR,proj(cam,np.c_[ov,np.zeros(len(ov))],cx,cy))
    r3=curve_d(RRI,proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy))
    # tower lean: the projected vertical through the low point must pass the top point
    M=R(*cam[3:6]);r4=[]
    for (t,l) in TW:
        X=at_z(cam,*l,cx,cy,0.0);q=proj(cam,np.array([X,X+[0,0,60]]),cx,cy);d=q[1]-q[0];d/=np.linalg.norm(d)
        v=np.array(t)-np.array(l);r4.append(d[0]*v[1]-d[1]*v[0])
    r4=np.array(r4)
    return (r1,r3,r4) if full else np.concatenate([r1,r3*2,r4*4,[p[7]*0.2,p[8]*0.2]])
out=[]
for F in (2500,4000,6000,9000,14000):
  best=None
  for yaw0 in (40,50,60,70):
    for pit in (-25,-35,-45):
      D=F*250/700;pr=math.radians(pit);yw=math.radians(yaw0)
      C=[-D*math.cos(pr)*math.cos(yw),-D*math.cos(pr)*math.sin(yw),-D*math.sin(pr)]
      p0=C+[yw,pr,math.radians(-3),0,0,0,1.1]
      try:sol=least_squares(res,p0,args=(F,),loss='soft_l1',f_scale=2,max_nfev=400)
      except Exception as e:continue
      c=(sol.fun**2).mean()
      if best is None or c<best[0]:best=(c,sol.x)
  r1,r3,r4=res(best[1],F,True);rm=lambda r:round(float(np.sqrt(np.median(r**2))),2)
  p=best[1];print(F,'cost',round(best[0],2),'grass',rm(r1),'rr',rm(r3),'lean px',np.round(r4,1),'ypr',np.round(np.degrees(p[3:6]),1),'s',round(p[9],3),'dist',round(float(np.linalg.norm(p[:3]))),flush=True)
  out.append((best[0],F,list(p)))
out.sort();c,F,p=out[0]
json.dump({'p':p[:6]+[F,1.0],'W':W,'H':H,'groundC':p[6:10],'oval':ground(p[6:10]).tolist()},open('camC8.json','w'))
