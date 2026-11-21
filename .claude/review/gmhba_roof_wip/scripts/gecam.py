import numpy as np
from scipy.optimize import least_squares
exec(open('pnp.py').read().split('X=np.array')[0])
X=np.array([p[1] for p in P],float);U=np.array([p[2] for p in P],float)
lx,ly=(144.3529-144.3546774)*87547,(-38.15795+38.1579976)*111320
def proj(q,cy):
  G,f,dh,dt,dx,dy=q
  h,t=np.radians(90+dh),np.radians(70+dt)
  d=np.array([np.sin(h)*np.sin(t),np.cos(h)*np.sin(t),-np.cos(t)])
  L=np.array([lx+dx,ly+dy,30-G]);C=L-150*d
  r=np.cross(d,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,d)
  v=X-C;z=v@d
  return np.c_[640+f*(v@r)/z,cy-f*(v@u)/z]
for cy in (277.5,292.5,320):
  for free in ('G,f','all'):
    def res(q):
      if free=='G,f':q=np.r_[q[:2],0,0,0,0]
      return (proj(q,cy)-U).ravel()
    q0=[10,800] if free=='G,f' else [10,800,0,0,0,0]
    s=least_squares(res,q0)
    e=np.linalg.norm(res(s.x).reshape(-1,2),axis=1)
    print(cy,free,np.round(s.x,2),'rms',round(np.sqrt((e**2).mean()),2),'max',round(e.max(),1))
print('--- fixed GE camera: fov35 vertical over 585, only ground ASL G free')
f=292.5/np.tan(np.radians(17.5))
s=least_squares(lambda q:(proj([q[0],f,0,0,0,0],292.5)-U).ravel(),[10])
pp=proj([s.x[0],f,0,0,0,0],292.5);e=pp-U
print('G',s.x,'f',round(f,1))
for p,ee,q in zip(P,e,pp):print(p[0],np.round(ee,1),round(np.hypot(*ee),1))
