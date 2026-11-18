import numpy as np,json
from scipy.optimize import least_squares
from meas import *
GW=np.load('grass_w.npy')
# resample grass contour by angle
a=np.arctan2(GW[:,1],GW[:,0]);r=np.hypot(GW[:,0],GW[:,1]);o=np.argsort(a);a,r=a[o],r[o]
A=np.linspace(-np.pi,np.pi,1440,endpoint=False);RG=np.interp(A,a,r,period=2*np.pi)
np.save('grass_polar.npy',RG)
def ring(d,z):
    # offset outward along the normal approx radial (ellipse-ish, fine for now)
    return np.stack([(RG+d)*np.cos(A),(RG+d)*np.sin(A),np.full_like(A,z)],1)
z0,y0,k=380,650,1.6
def zp(L):return np.array([(650+x/k,380+y/k) for x,y in L])
WALK=zp([(160,238),(600,268),(800,305),(1000,352),(1150,430),(1230,490)])
BACK=zp([(160,125),(480,120),(800,170),(1000,225),(1150,310),(1240,400)])
def fit(Pts):
    def res(q):
        pp=pr(ring(*q));return np.array([np.min(np.hypot(*(pp-p).T)) for p in Pts])
    s=least_squares(res,[10,6]);return s.x,np.sqrt(np.mean(s.fun**2)),s.fun
for nm,P in (('walk',WALK),('back',BACK)):
    x,rms,f=fit(P);print(nm,x.round(2),'rms',rms.round(1),f.round(1))
