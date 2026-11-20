import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if (t=='t' and 240<=x<=770)],float)
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15]
CEN=np.array([537,336.0])
RR=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126)])
RRI=np.array([(497,553),(576,525),(655,497),(734,459),(813,421),(892,396),(971,371)],float)
TW=[((549,279),(561,482)),((897,147),(913,374)),((205,100),(212,250)),((510,22),(517,165))]
def ground(p):
    th,dx,dy,A,B=p[7:12];a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)])
    ov=np.outer(PN[:,0]*A,U)+np.outer(PN[:,1]*B,V)+[dx,dy];return np.vstack([ov,ov[:1]]),np.array([dx,dy])
def res(p,full=False):
    cam=p[:7];ov,c=ground(p);Ht=p[12];tw=p[13:21].reshape(4,2);lz=np.abs(p[21:25])
    r1=curve_d(GR,proj(cam,np.c_[ov,np.zeros(len(ov))],cx,cy))
    r2=(proj(cam,np.array([[c[0],c[1],0]]),cx,cy)[0]-CEN)*3
    r3=curve_d(RRI,proj(cam,np.c_[RR,np.zeros(len(RR))],cx,cy))*2
    r4=[]
    for k,(h,l) in enumerate(TW):
        a=proj(cam,np.array([[*tw[k],Ht],[*tw[k],lz[k]]]),cx,cy);r4+=list(a[0]-h)+list(a[1]-l)
    r4=np.array(r4)
    out=np.concatenate([r1,r2,r3,r4*2,[p[8]*2,p[9]*2]])
    return (r1,r2/3,r3/2,r4) if full else out
best=None
for d,f0 in [(500,1200),(900,2000),(1800,4000),(4000,9000)]:
  for yaw0 in np.radians([50,65]):
    p0=[-d*0.5,-d*0.65,d*0.55,yaw0,-0.6,0,f0,0,0,0,95,65,60,-60,-110,110,-80,-120,60,40,110,15,15,15,15]
    sol=least_squares(res,p0,loss='soft_l1',f_scale=3);c=(sol.fun**2).mean();print(d,round(math.degrees(yaw0)),round(c,2),round(sol.x[6]),np.round(sol.x[10:12],1),flush=True)
    if best is None or c<best[0]:best=(c,sol.x)
p=best[1];r1,r2,r3,r4=res(p,True)
rm=lambda r:round(float(np.sqrt(np.median(r**2))),2)
print('grass',rm(r1),'centre',np.round(r2,1),'roberts',rm(r3),'towers',rm(r4))
print('ground th dx dy A B',np.round([math.degrees(p[7]),*p[8:12]],2),'Ht',round(p[12],1))
print('towers',np.round(p[13:21].reshape(4,2),1),'lowz',np.round(np.abs(p[21:25]),1))
print('cam',np.round(p[:3],1),np.round(np.degrees(p[3:6]),2),round(p[6],1))
ov,c=ground(p)
json.dump({'p':list(p[:7])+[1.0],'W':W,'H':H,'ground':list(p[7:12]),'oval':ov.tolist(),'tw':p[13:21].reshape(4,2).tolist(),'Ht':p[12],'lowz':list(np.abs(p[21:25]))},open('camC.json','w'))
