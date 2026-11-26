# pinhole camera of a ge_compare view (east, north, up metres from the model origin); F px for the 1280x720 capture
import math, numpy as np, json, sys
sys.path.insert(0,'/home/user/Afl-auto-battler/tools/grounds/cazalys/work'); import fence_ge as fg
F=fg.F
def pose(v, dtilt=0.0, dd=0.0, dz=0.0):
    e,n,u=v.get('at',[0,0,0]); h=math.radians(v['h']); t=math.radians(v['t']+dtilt); d=v['d']+dd
    dirv=np.array([math.sin(t)*math.sin(h), math.sin(t)*math.cos(h), -math.cos(t)])
    T=np.array([e,n,u+dz]); C=T-d*dirv; return C,T
def project(v,P,**k):
    C,T=pose(v,**k); f=(T-C)/np.linalg.norm(T-C); r=np.cross(f,[0,0,1.0]); r/=np.linalg.norm(r); up=np.cross(r,f)
    Q=np.asarray(P,float)-C; x=Q@r; y=Q@up; z=Q@f
    return np.stack([640+F*x/z, 360-F*y/z],1), z
