import numpy as np,json,math
from camlib import *
JA=json.load(open('camA_final.json'));CAM=json.load(open('camC13.json'))['p'][:7];CX,CY=512,314.5
th,dx,dy,L,B=JA['ground']
a0=math.radians(172);U0=np.array([math.cos(a0),math.sin(a0)]);V0=np.array([-math.sin(a0),math.cos(a0)])
P0=PITCH-PITCH.mean(0);PN=np.c_[P0@U0/92.65,P0@V0/64.15];ext=PN[:,0].max()
a=a0+th;U=np.array([math.cos(a),math.sin(a)]);V=np.array([-math.sin(a),math.cos(a)]);C0=np.array([dx,dy])
OV=np.outer(PN[:,0]*L/ext,U)+np.outer(PN[:,1]*B,V)+C0
# boundary polar about C0, world angle in degrees
_ang=np.degrees(np.arctan2(OV[:,1]-C0[1],OV[:,0]-C0[0]));_r=np.hypot(OV[:,0]-C0[0],OV[:,1]-C0[1]);_o=np.argsort(_ang)
PA=np.radians(_ang[_o]);PR=_r[_o]
def rp(adeg):return float(np.interp(math.radians(adeg),PA,PR,period=2*math.pi))
def bp(u,v,z=0.0):
    X=at_z(CAM,u,v,CX,CY,z);d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));r=math.hypot(*d);return X,ad,r,r-rp(ad)
def pr(X):return proj(CAM,np.atleast_2d(X),CX,CY)
FJ=json.load(open('fenceA.json'));_co=np.array(FJ['co']);_K=FJ['K']
def rf(ad):t=math.radians(ad);return sum(_co[k]*math.cos(k*t) for k in range(_K+1))+sum(_co[_K+k]*math.sin(k*t) for k in range(1,_K+1))
def pol(u,v,z):X,ad,r,_=bp(u,v,z);return round(ad,1),round(r-rf(ad),1),z
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
