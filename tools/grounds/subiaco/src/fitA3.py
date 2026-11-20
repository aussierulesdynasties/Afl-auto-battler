import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1200,676;cx,cy=W/2,H/2
E=json.load(open('edgeA.json'))
GR=np.array([(x,y) for x,y,t in E],float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15]  # unit oval in its own axes
SQN=np.array([[1,1],[1,-1],[-1,-1],[-1,1]],float)*25
SQI=np.array([(535,274.3),(691.3,283),(685.5,391.8),(513.8,380.5)],float)
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126),way(951696125)])
RRI=np.array([(100,611),(400,618),(700,625),(1000,633)],float)
RAIL=[way(4936512),way(8112606)]
RAILI=np.array([(0,100),(300,78),(600,52),(900,28),(1150,8)],float)
def ground(p):
    th,dx,dy,A,B=p[7:12];a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)])
    ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*B,V)+[dx,dy];sq=np.outer(SQN[:,0],U)+np.outer(SQN[:,1],V)+[dx,dy]
    return np.vstack([ov,ov[:1]]),sq
def res(p,full=False):
    cam=p[:7];ov,sq=ground(p)
    r1=curve_d(GR,proj(cam,np.c_[ov,np.zeros(len(ov))],cx,cy))
    q=proj(cam,np.c_[sq,np.zeros(4)],cx,cy)
    best=None
    for k in range(4):
        d=(q[[(i+k)%4 for i in range(4)]]-SQI).ravel()
        if best is None or (d**2).sum()<(best**2).sum():best=d
    r2=best*2
    r3=curve_d(RRI,proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy))
    r4=np.min([curve_d(RAILI,proj(cam,np.c_[w,np.zeros(len(w))],cx,cy)) for w in RAIL],0)*0.3
    out=np.concatenate([r1,r2,r3,r4])
    return (r1,r2/2,r3,r4/0.3) if full else out
best=None
for yaw0 in np.radians([80,95]):
  for d,f0 in [(400,1000),(700,1600),(1500,3500)]:
    p0=[0,-d*0.8,d*0.6,yaw0,-0.7,0,f0,0,0,0,90,63]
    try:sol=least_squares(res,p0,loss='soft_l1',f_scale=3)
    except Exception as e:print(e);continue
    c=(sol.fun**2).mean();print(round(math.degrees(yaw0)),d,round(c,2),flush=True)
    if best is None or c<best[0]:best=(c,sol.x)
p=best[1];r1,r2,r3,r4=res(p,True)
rm=lambda r:round(float(np.sqrt(np.median(r**2))),2)
print('median-rms grass',rm(r1),'square',rm(r2),'roberts',rm(r3),'rail',rm(r4))
print('ground th dx dy A B',np.round([math.degrees(p[7]),*p[8:12]],2))
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1))
ov,sq=ground(p)
json.dump({'p':list(p[:7])+[1.0],'W':W,'H':H,'ground':list(p[7:12]),'oval':ov.tolist(),'square':sq.tolist()},open('camA.json','w'))
