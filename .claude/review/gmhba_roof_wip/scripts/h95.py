import numpy as np,sys
from scipy.spatial.transform import Rotation as R
p=np.load('cam_svw.npy');C=p[:3];f=1280/2/np.tan(np.radians(37.5))
Rm=R.from_euler('ZYX',p[3:]).as_matrix()
def proj(X):
    c=Rm.T@(np.array(X)-C);return 640-f*c[1]/c[0],292.5-f*c[2]/c[0]
def ray(u,v):
    d=Rm@np.array([1,(640-u)/f,(292.5-v)/f]);return d/np.linalg.norm(d)
for X in [(-120,-44.8,24),(-120,-3.4,24),(-120,-44.8,0),(-120,-3.4,0),(-122.5,-59.2,74.7)]:print(X,np.round(proj(X),1))
def at_x(u,v,x):
    d=ray(u,v);t=(x-C[0])/d[0];P=C+t*d;return np.round(P,2)
def wx(y):return -122.6 if y<44 else -122.6+(y-44)/48*1.2
def at_edge(u,v):
    x=-122.6
    for _ in range(20):
        P=at_x(u,v,x);x=wx(P[1])
    return P
print('canopy W edge (top line)')
for u,v in [(0,257.5),(100,259.2),(200,260.8),(300,262.5)]:print(u,v,at_edge(u,v))
print('block top / sign at x=-121 and -119.2')
for n,u,v in [('blkTL',600,250),('blkTR',669,250),('signTL',591,280),('signBR',677.5,309)]:print(n,at_x(u,v,-121),at_x(u,v,-119.2))
