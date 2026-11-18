import numpy as np,json,math
from scipy.optimize import least_squares
from camlib import *
W,H=1024,629;cx,cy=W/2,H/2
E=json.load(open('edgeC.json'))
GR=np.array([(x,y) for x,y,t in E if (t=='t' and 240<=x<=770)],float)
PATH=(np.vstack([way(1387282522),way(44626848)[::-1] if False else way(44626848),way(128189143)[::-1]]))
# check ordering doesn't matter for point-to-curve distance; just a point cloud along the path
SUBW=np.vstack([way(1430111014),way(951696127),way(1374562961),way(951696126)])
SUBI=np.array([(497,553),(576,525),(655,497),(734,459),(813,421),(892,396),(971,371)],float)
SUBE=np.vstack([way(1425042816),way(1189765490)])
SUBEI=np.array([(820,86),(861,80),(926,70),(991,60),(1024,55)],float)
PATHI=np.array([(800,625),(850,593),(950,535),(1017,498)],float)
# towers: head (u,v), low (u,v), low_is_ground
TW=[((549,279),(561,482),False),((897,147),(913,374),False),((205,100),(212,250),False),((510,22),(517,165),False)]
def unpack(p):
    cam=p[:7];s=p[7];Ht=p[8];tw=p[9:17].reshape(4,2);lz=np.abs(p[17:21]);return cam,s,Ht,tw,lz
def res(p,full=False):
    global cx,cy
    cx,cy=W/2+p[21],H/2+p[22]
    cam,s,Ht,tw,lz=unpack(p)
    pc=np.vstack([PITCH*s,PITCH[:1]*s]);pp=proj(cam,np.c_[pc,np.zeros(len(pc))],cx,cy)
    r1=curve_d(GR,pp)
    pe=proj(cam,np.c_[SUBE,np.zeros(len(SUBE))],cx,cy);r2=curve_d(SUBEI,pe)*2
    ps=proj(cam,np.c_[SUBW,np.zeros(len(SUBW))],cx,cy);r2=np.concatenate([r2,curve_d(SUBI,ps)*2])
    r3=[]
    for k,(h,l,g) in enumerate(TW):
        a=proj(cam,np.array([[*tw[k],Ht],[*tw[k],0 if g else lz[k]]]),cx,cy)
        r3+=list((a[0]-h)*2)+list((a[1]-l)*2)
    out=np.concatenate([r1,r2,r3,[(s-1)*2000,p[21]*0.01,p[22]*0.01]])
    return (r1,r2,np.array(r3)) if full else out
best=None
P4=json.load(open('camC.json'))['p'][:21]
for cxy in [(0,0),(-150,0),(150,0),(0,-150),(0,150)]:
    p0=list(P4)+list(cxy);p0[7]=1.0
    sol=least_squares(res,p0,loss='soft_l1',f_scale=3);c=(sol.fun**2).mean();print(cxy,round(c,2),np.round(sol.x[21:23],1),round(sol.x[6]),flush=True)
    if best is None or c<best[0]:best=(c,sol.x)
p=best[1];r1,r2,r3=res(p,True)
r2b=r2;print('grass rms',np.sqrt((r1**2).mean()),'road rms',np.sqrt((r2**2).mean())/2,'tower rms',np.sqrt((r3**2).mean())/2)
cam,s,Ht,tw,lz=unpack(p);print('cam',np.round(cam[:3],1),np.round(np.degrees(cam[3:6]),2),round(cam[6],1),'s',round(s,3),'H',round(Ht,1));print('towers',np.round(tw,1),'lowz',np.round(lz,1))
print('pp',np.round(p[21:23],1));json.dump({'p':list(p),'W':W,'H':H,'cx':W/2+p[21],'cy':H/2+p[22]},open('camC.json','w'))
