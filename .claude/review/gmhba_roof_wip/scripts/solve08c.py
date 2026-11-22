import numpy as np
from scipy.optimize import least_squares
P=lambda h:np.array([[-120,-3.4,24],[-120,-44.8,24],[-120,-3.4,h],[-120,-44.8,h],[-126,22.2,22.7],[-126,-3.4,22.7],
   [-122.5,-59.2,74.7],[-122.5,-59.2,0],[-57.8,108.0,74.7],[27.7,-118.6,74.7],[104.5,68.7,74.7]])
px=np.array([[4963,2285],[5952,2388],[4960,2620],[5935,2730],[4237,2308],[4851,2324],[6220,1188],[6162,2898],[3890,1100],[7010,1088],[5058,1080]],float)
def proj(q,X):
    C=q[:3];az0,f,v0=q[3],q[4],q[5];d=X-C
    az=np.arctan2(d[:,1],d[:,0]);u=(az0-az+np.pi)%(2*np.pi)-np.pi   # clockwise to the right
    el=np.arctan2(d[:,2],np.hypot(d[:,0],d[:,1]))
    return np.stack([3879+f*u,v0-f*np.tan(el)],1)
res=lambda q:(proj(q,P(q[6]))-px).ravel()
best=None
for cx0,cy0 in((-400,-200),(-500,-50),(-350,-300),(-600,-250)):
  for z in(80,150,250):
    q0=[cx0,cy0,z,np.arctan2(0-cy0,-110-cx0),4000,1050,5]
    r=least_squares(res,q0)
    if best is None or r.cost<best.cost:best=r
q=best.x;e=res(q).reshape(-1,2)
print('cam',np.round(q[:3],1),'az0',round(np.degrees(q[3]),2),'f',round(q[4]),'v0',round(q[5]),'band_z',round(q[6],2))
print('rms',round(np.sqrt((e**2).sum(1).mean()),1),'per pt',np.round(np.hypot(*e.T),1))
np.save('cam08.npy',q)
for nm,X in (('NWcurve',[-95,80,22]),('block',[-121,10,15])):
  d=np.array(X)-q[:3];print(nm,'bearing cam->pt (compass)',round((90-np.degrees(np.arctan2(d[1],d[0])))%360,1),'dist',round(np.hypot(d[0],d[1])))
