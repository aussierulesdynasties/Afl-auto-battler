# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, math, json
F7=0.364  # m/px at 3000 m, 7y
def focal(fovy): return 3000/F7*math.tan(math.radians(3.5))/math.tan(math.radians(fovy/2))
def camera(T,h,t,d,fovy):
    h,t=math.radians(h),math.radians(t)
    fwd=np.array([math.sin(t)*math.sin(h),math.sin(t)*math.cos(h),-math.cos(t)])
    C=np.array(T,float)-d*fwd
    right=np.array([math.cos(h),-math.sin(h),0.0])
    up=np.cross(right,fwd)
    return C,fwd,right,up,focal(fovy)
def project(cam,P):
    C,fw,ri,up,f=cam; V=np.asarray(P,float)-C
    z=V@fw; return np.c_[640+f*(V@ri)/z, 360-f*(V@up)/z]
