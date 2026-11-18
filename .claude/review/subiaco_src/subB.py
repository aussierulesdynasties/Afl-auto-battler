import numpy as np,json,math
from camlib import *
JA=json.load(open('camA_final.json'));CAM=json.load(open('camB.json'))['p'][:7];CX,CY=500,300
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
def pol_rake(u,v,s,z0=0.5,dz=0.0):
    # point on the ray where z = z0 + s*d (d = distance beyond the fence) + dz
    C=np.array(CAM[:3]);w=ray(CAM,u,v,CX,CY)
    lo,hi=10.0,3000.0
    def f(t):
        X=C+t*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return X[2]-(z0+s*(math.hypot(*d)-rf(ad))+dz)
    for _ in range(80):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0:hi=m
        else:lo=m
    X=C+lo*w;d=X[:2]-C0;ad=math.degrees(math.atan2(d[1],d[0]));return round(ad,1),round(math.hypot(*d)-rf(ad),1),round(X[2],1)
