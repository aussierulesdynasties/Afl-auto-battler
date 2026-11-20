# Google Earth URL camera -> local ENU metres (x east, y north, z up relative to target altitude 'a').
import math,numpy as np
def cam(h,t,d,fovy=35.0,W=1920,H=1080,tz=0.0,tx=0.0,ty=0.0):
    hr,tr=math.radians(h),math.radians(t)
    fwd=np.array([math.sin(hr)*math.sin(tr),math.cos(hr)*math.sin(tr),-math.cos(tr)])
    C=np.array([tx,ty,tz])-d*fwd
    right=np.array([math.cos(hr),-math.sin(hr),0.0])
    up=np.cross(right,fwd)
    f=(H/2)/math.tan(math.radians(fovy)/2)
    return dict(C=C,fwd=fwd,right=right,up=up,f=f,W=W,H=H)
def proj(c,X):
    d=np.asarray(X,float)-c['C'];z=d@c['fwd']
    return np.array([c['W']/2+c['f']*(d@c['right'])/z, c['H']/2-c['f']*(d@c['up'])/z])
