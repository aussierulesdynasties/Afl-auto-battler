import numpy as np, sys
from camsolve import *
q=np.load('cam_so.npy') if len(sys.argv)<2 else None
def ray(q,u,v):
    c=campos(q); f,rr,uu=Rm(*q[3:6]); F=q[6]
    d=f+((u-W/2)/F)*rr+(-(v-H/2)/F)*uu; return c,d
def hit_plane_y(q,u,v,Y):
    c,d=ray(q,u,v); t=(Y-c[1])/d[1]; return c+t*d
