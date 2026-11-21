import numpy as np,math,json
from scipy.optimize import least_squares
from cam import *
# unknowns: p[0:9] camera, L1, L2, hg, hb
obs=[]  # (fn(q)->xyz, (u,v))
def add(f,uv):obs.append((f,uv))
for (x,y),uv in [((-25,25),(570.7,596.7)),((25,25),(829,576)),((25,-25),(903.3,689.3)),((-25,-25),(580.7,723.3)),((0,0),(721.7,639))]:
    add(lambda q,x=x,y=y:(x,y,0),uv)
for x,uv in [(-9.6,(753.75,969.5)),(-3.2,(813.25,959.5)),(3.2,(873.75,950)),(9.6,(930,941.75))]:add(lambda q,x=x:(x,-q[0],0),uv)
for x,uv in [(-3.2,(794.5,908)),(3.2,(853,900.75))]:add(lambda q,x=x:(x,-q[0]+9,0),uv)
for x,uv in [(-3.2,(815,837)),(3.2,(876.25,829))]:add(lambda q,x=x:(x,-q[0],q[2]),uv)
for x,uv in [(-9.6,(753.25,903)),(9.6,(932.5,877))]:add(lambda q,x=x:(x,-q[0],q[3]),uv)
for x,uv in [(-9.6,(627.5,499.7)),(-3.2,(655,496.7)),(3.2,(682,495)),(9.6,(709.2,493.3))]:add(lambda q,x=x:(x,q[1],0),uv)
for x,uv in [(-3.2,(657.5,508.8)),(3.2,(687,507))]:add(lambda q,x=x:(x,q[1]-9,0),uv)
Y=np.array([o[1] for o in obs])
FREEPP=True
def unpack(s):
    p=list(s[:9]) if FREEPP else list(s[:7])+[W/2,H/2]
    return np.array(p),s[9:] if FREEPP else s[7:]
def res(s):
    p,q=unpack(s);X=np.array([o[0](q) for o in obs]);return (proj(p,X)-Y).ravel()
best=None
for FREEPP in (False,True):
  for yaw0 in np.radians([60,75,90,105,120]):
    for h in (80,120,180):
        s0=[0,-200,h,yaw0,-0.4,0,1500]+([W/2,H/2] if FREEPP else [])+[80,80,15,8]
        try:s=least_squares(res,s0,max_nfev=4000)
        except Exception:continue
        rms=math.sqrt((s.fun**2).mean())
        if best is None or rms<best[0]-0.01 or (FREEPP and best[2]==False and rms<best[0]+0.3):best=(rms,s,FREEPP)
  FP=FREEPP
rms,s,FREEPP=best;p,q=unpack(s.x)
print('rms',round(rms,2),'freepp',FREEPP);print('cam',np.round(p,2));print('L1 L2 hg hb',np.round(q,2))
print(np.round(s.fun.reshape(-1,2),1))
json.dump({'p':list(p),'q':list(q)},open('cam.json','w'))
