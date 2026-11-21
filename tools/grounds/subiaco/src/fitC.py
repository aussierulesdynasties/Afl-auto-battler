import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if (t=='t' and 240<=x<=770)],float)
PATH=(np.vstack([way(1387282522),way(44626848)[::-1] if False else way(44626848),way(128189143)[::-1]]))
# check ordering doesn't matter for point-to-curve distance; just a point cloud along the path
PATHI=np.array([(800,625),(850,593),(950,535),(1017,498)],float)
# towers: head (u,v), low (u,v), low_is_ground
TW=[((550,272),(563,483),False),((897,148),(912,372),False),((205,100),(212,250),False),((510,22),(517,165),False)]
def unpack(p):
    cam=p[:7];s=p[7];Ht=p[8];tw=p[9:17].reshape(4,2);lz=np.abs(p[17:21]);return cam,s,Ht,tw,lz
def res(p,full=False):
    cam,s,Ht,tw,lz=unpack(p)
    pc=np.vstack([PITCH*s,PITCH[:1]*s]);pp=proj(cam,np.c_[pc,np.zeros(len(pc))],cx,cy)
    r1=curve_d(GR,pp)
    ph=proj(cam,np.c_[PATH,np.zeros(len(PATH))],cx,cy);r2=curve_d(PATHI,ph)*2
    r3=[]
    for k,(h,l,g) in enumerate(TW):
        a=proj(cam,np.array([[*tw[k],Ht],[*tw[k],0 if g else lz[k]]]),cx,cy)
        r3+=list((a[0]-h)*2)+list((a[1]-l)*2)
    out=np.concatenate([r1,r2,r3,[(s-1)*400]])
    return (r1,r2,np.array(r3)) if full else out
best=None
for yaw0 in np.radians([-110,-90,-70]):
  for d in [450,700]:
    p0=[0,d*0.8,d*0.6,yaw0,-0.6,0,1000,1.0,55,  20,90, -120,40, 120,-60, 10,-110, 15,15,15,15]
    try:s=least_squares(res,p0,loss='soft_l1',f_scale=3)
    except Exception as e:continue
    c=(s.fun**2).mean()
    if best is None or c<best[0]:best=(c,s.x)
p=best[1];r1,r2,r3=res(p,True)
print('grass rms',np.sqrt((r1**2).mean()),'path rms',np.sqrt((r2**2).mean())/2,'tower rms',np.sqrt((r3**2).mean())/2)
cam,s,Ht,tw,lz=unpack(p);print('cam',np.round(cam[:3],1),np.round(np.degrees(cam[3:6]),2),round(cam[6],1),'s',round(s,3),'H',round(Ht,1));print('towers',np.round(tw,1),'lowz',np.round(lz,1))
json.dump({'p':list(p),'W':W,'H':H},open('camC.json','w'))
