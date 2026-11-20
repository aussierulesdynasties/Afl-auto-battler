import numpy as np
W,H=1200,675
def axes(yaw,pitch,roll):
    # yaw: compass heading of view (0=north,+east), pitch: + up
    f=np.array([np.cos(pitch)*np.sin(yaw),np.cos(pitch)*np.cos(yaw),np.sin(pitch)])
    r=np.array([np.cos(yaw),-np.sin(yaw),0.0])
    u=np.cross(r,f)
    cr,sr=np.cos(roll),np.sin(roll)
    r2=cr*r+sr*u;u2=-sr*r+cr*u
    return f,r2,u2
def proj(P,p):
    C=p[0:3];f,r,u=axes(*p[3:6]);fl=p[6];cx,cy=p[7],p[8]
    d=np.atleast_2d(P)-C
    z=d@f;x=d@r;y=d@u
    return np.stack([cx+fl*x/z,cy-fl*y/z],1)
def ray(uv,p):
    C=p[0:3];f,r,u=axes(*p[3:6]);fl=p[6];cx,cy=p[7],p[8]
    d=f+(uv[0]-cx)/fl*r-(uv[1]-cy)/fl*u
    return C,d/np.linalg.norm(d)
def at_z(uv,p,z=0):
    C,d=ray(uv,p);t=(z-C[2])/d[2];return C+t*d
import json as _j
def load():
    J=_j.load(open(__file__.replace('cam.py','cam.json')));return J['p']
def hz(x,y,v,p):
    from scipy.optimize import brentq
    return brentq(lambda z: proj(np.array([x,y,z]),p)[0][1]-v,-20,200)
def P(x,y,z,p): return proj(np.array([x,y,z],float),p)[0].round(1)
