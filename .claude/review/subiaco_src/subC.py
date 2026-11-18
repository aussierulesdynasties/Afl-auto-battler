# camera C helpers, C frame (oval scaled by s vs OSM; model built here, then scaled by 1/s about C0)
import numpy as np,json,math
from camlib import *
JC=json.load(open('camC_final.json'));CAM=JC['p'][:7];CX,CY=512,314.5
th,dx,dy,SC=JC['groundC'];C0=np.array([dx,dy]);OV=np.array(JC['oval'])[:-1]
_ang=np.degrees(np.arctan2(OV[:,1]-dy,OV[:,0]-dx));_r=np.hypot(OV[:,0]-dx,OV[:,1]-dy);_o=np.argsort(_ang)
PA=np.radians(_ang[_o]);PR=_r[_o]
def rp(ad):return float(np.interp(math.radians(ad),PA,PR,period=2*math.pi))
MG=2.4*SC
def rf(ad):return rp(ad)+MG
def bp(u,v,z=0.0):
    X=at_z(CAM,u,v,CX,CY,z);d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));r=math.hypot(*d);return X,ad,r,r-rf(ad)
def pr(X):return proj(CAM,np.atleast_2d(X),CX,CY)
def pol(u,v,z):X,ad,r,_=bp(u,v,z);return [round(ad,2),round(r-rf(ad),2),z]
def vpair(foot,top):
    X=bp(*foot,0)[0];hs=np.linspace(0,150,3001);h=min(hs,key=lambda h:np.hypot(*(pr([X[0],X[1],h])[0]-top)))
    d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return [round(ad,2),round(math.hypot(*d)-rf(ad),2),round(float(h),2)]
def at_d(u,v,dt=1.0):
    C=np.array(CAM[:3]);w=ray(CAM,u,v,CX,CY)
    def f(t):X=C+t*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return math.hypot(*d)-rf(ad)-dt
    ts=np.linspace(10,4000,4000);fs=[f(t) for t in ts]
    for i in range(len(ts)-1):
        if fs[i]>0>=fs[i+1]:
            a,b=ts[i],ts[i+1]
            for _ in range(50):
                m=(a+b)/2
                if f(m)>0:a=m
                else:b=m
            X=C+a*w;d=X[:2]-C0;return [round(math.degrees(math.atan2(d[1],d[0])),2),dt,round(float(X[2]),2)]
def pol_rake(u,v,s,z0=0.5,dz=0.0):
    C=np.array(CAM[:3]);w=ray(CAM,u,v,CX,CY);lo,hi=10.0,4000.0
    def f(t):
        X=C+t*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return X[2]-(z0+s*(math.hypot(*d)-rf(ad))+dz)
    for _ in range(80):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0:hi=m
        else:lo=m
    X=C+lo*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return [round(ad,2),round(math.hypot(*d)-rf(ad),2),round(float(X[2]),2)]
def cross(u,v,dt,zt):
    C=np.array(CAM[:3]);w=ray(CAM,u,v,CX,CY);ts=np.linspace(10,4000,8000)
    def f(t):X=C+t*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return math.hypot(*d)-rf(ad)-dt
    fs=np.array([f(t) for t in ts]);out=[]
    for i in np.where(np.sign(fs[:-1])!=np.sign(fs[1:]))[0]:
        X=C+ts[i]*w;d=X[:2]-C0;out.append([round(math.degrees(math.atan2(d[1],d[0])),2),dt,round(float(X[2]),2)])
    return min(out,key=lambda p:abs(p[2]-zt)) if out else None
def pol_rake(u,v,s,z0=0.5,dz=0.0):
    # scan the ray for z = z0 + s*d + dz with the point in the stand band (0 < d < 90)
    C=np.array(CAM[:3]);w=ray(CAM,u,v,CX,CY);ts=np.linspace(10,4000,16000)
    X=C[None]+ts[:,None]*w[None];dd=X[:,:2]-C0;ad=np.degrees(np.arctan2(dd[:,1],dd[:,0]));D=np.hypot(dd[:,0],dd[:,1])-np.array([rf(a) for a in ad])
    f=X[:,2]-(z0+s*D+dz);ok=(D>0)&(D<90)
    idx=[i for i in np.where(np.sign(f[:-1])!=np.sign(f[1:]))[0] if ok[i]]
    if not idx:return None
    i=idx[0];return [round(float(ad[i]),2),round(float(D[i]),2),round(float(X[i,2]),2)]
