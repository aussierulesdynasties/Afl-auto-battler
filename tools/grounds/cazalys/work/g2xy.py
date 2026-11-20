# GE pixel -> ground xy (z=Z) for a capture: python work/g2xy.py h t d u,v [u,v ...] [--z Z]
import sys,numpy as np,earthcam
a=sys.argv[1:];Z=0.0
if '--z' in a: i=a.index('--z');Z=float(a[i+1]);a=a[:i]+a[i+2:]
h,t,d=map(float,a[:3]);c=earthcam.cam(h,t,d)
for s in a[3:]:
  u,v=map(float,s.split(','));r=c['fwd']+(u-c['W']/2)/c['f']*c['right']-(v-c['H']/2)/c['f']*c['up']
  k=(Z-c['C'][2])/r[2];p=c['C']+k*r;print(s,'->',np.round(p[:2],1))
