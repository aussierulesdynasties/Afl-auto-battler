import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1200,676;cx,cy=W/2,H/2
E=json.load(open('edgeA.json'))
GR=np.array([(x,y) for x,y,t in E],float)
a=math.radians(172);u=np.array([math.cos(a),math.sin(a)]);v=np.array([-math.sin(a),math.cos(a)])
SQ=np.array([25*u+25*v,25*u-25*v,-25*u-25*v,-25*u+25*v,25*u+25*v])
SQI=np.array([(535,274.3),(691.3,283),(685.5,391.8),(513.8,380.5)],float)
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126),way(951696125)])
RRI=np.array([(100,611),(400,618),(700,625),(1000,633)],float)
RAIL=[way(4936512),way(8112606)]
RAILI=np.array([(0,100),(300,78),(600,52),(900,28),(1150,8)],float)
def res(p,full=False):
    cam=p[:7];s=p[7];th,dx,dy=p[8:11];c,sn=math.cos(th),math.sin(th);SQr=SQ@np.array([[c,sn],[-sn,c]])+[dx,dy]
    pc=np.vstack([PITCH*s,PITCH[:1]*s]);pp=proj(cam,np.c_[pc,np.zeros(len(pc))],cx,cy)
    r1=curve_d(GR,pp)
    q=proj(cam,np.c_[SQr,np.zeros(5)],cx,cy);r2=curve_d(SQI,q)*3
    q=proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy);r3=curve_d(RRI,q)
    r4=np.min([curve_d(RAILI,proj(cam,np.c_[w,np.zeros(len(w))],cx,cy)) for w in RAIL],0)*0.3
    out=np.concatenate([r1,r2,r3,r4,[(s-1)*200,th*20,dx*0.2,dy*0.2]])
    return (r1,r2/3,r3,r4/0.3,s) if full else out
best=None
for yaw0 in np.radians([90]):
  for d,f0 in [(500,1200),(1800,4000)]:
    p0=[0,-d*0.8,d*0.6,yaw0,-0.6,0,f0,1.0,0,0,0]
    try:sol=least_squares(res,p0,loss='soft_l1',f_scale=3)
    except Exception as e:print(e);continue
    c=(sol.fun**2).mean();print(round(math.degrees(yaw0)),d,round(c,2),flush=True)
    if best is None or c<best[0]:best=(c,sol.x)
p=best[1];r1,r2,r3,r4,s=res(p,True)
rm=lambda r:round(float(np.sqrt(np.median(r**2))),2)
print('median-rms grass',rm(r1),'square',rm(r2),'roberts',rm(r3),'rail',rm(r4),'s',round(s,3))
print('sq th dx dy',np.round([math.degrees(p[8]),p[9],p[10]],2));print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1))
json.dump({'p':list(p),'W':W,'H':H},open('camA.json','w'))
