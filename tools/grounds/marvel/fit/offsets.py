import numpy as np
from shapely.geometry import Polygon,LinearRing
def se_r(th,a,b,n):return 1/((np.abs(np.cos(th))/a)**n+(np.abs(np.sin(th))/b)**n)**(1/n)
TH=np.linspace(-np.pi,np.pi,4000,endpoint=False)
OA,OB,ON=118.0,108.5,2.5;PA,PB,PN=86.0,72.0,2.2
r0=se_r(TH,OA,OB,ON);base=Polygon(np.c_[r0*np.cos(TH),r0*np.sin(TH)])
def dev(r,o):
    ring=LinearRing(np.c_[r*np.cos(TH),r*np.sin(TH)]);ex=base.buffer(o,resolution=64,join_style=1).exterior
    d=np.array([ex.distance(__import__('shapely').geometry.Point(p)) for p in np.array(ring.coords)[::10]])
    return d.max(),np.median(d)
print('outer wall rings (radial offset of the superellipse vs exact offset):')
for o in(-0.4,-0.6,-3,-4,-5,-6):print('  o=%5.1f  max %.2f m  median %.2f m'%(o,*dev(r0+o,o)))
rp=se_r(TH,PA,PB,PN)+2.0;D=r0-6.0-rp
print('tier rings (blend of the pitch superellipse and the wall) vs the nearest exact offset of the wall:')
for nm,f in(('tier1 front',0.0),('tier1 back / tier3 front',0.62),('tier2 front',0.40),('tier2 back',0.80),('tier3 back',1.0)):
    r=rp+D*f;o=np.mean(r-r0);print('  %-26s mean offset %6.1f m  max dev %.2f m  median %.2f m'%(nm,o,*dev(r,o)))
