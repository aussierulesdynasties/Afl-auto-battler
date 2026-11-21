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
V={'NL_pole':[(145,602),(167.5,780),(191,930),(209,1030)],'NL_lat':[(197,720),(202.5,730),(213.8,830),(220,847)],
'FL_pole':[(395,311),(402.5,410),(411.25,500)],'FL_2':[(343.75,410),(351.25,460),(356.25,510)],
'FR_pole':[(896.25,300),(895.5,385),(893.75,480)],'FR_2':[(939.5,372.5),(937,435),(935,495)],
'R_pole':[(1360,511.7),(1351.7,606.7),(1338.3,706.7)],'R_lat':[(1296.7,580),(1283.3,673.3),(1273.3,746.7)]}
NQ=4;k=NQ
for nm,pts in V.items():
    bx=k;k+=2
    for uv in pts:
        add(lambda q,bx=bx,iz=k:(q[bx],q[bx+1],q[iz]),uv);k+=1
NEXTRA=k-NQ
Y=np.array([o[1] for o in obs])
FREEPP=True
def unpack(s):
    p=list(s[:9]) if FREEPP else list(s[:7])+[W/2,H/2]
    return np.array(p),s[9:] if FREEPP else s[7:]
def res(s):
    p,q=unpack(s);X=np.array([o[0](q) for o in obs]);return (proj(p,X)-Y).ravel()
import json as _j
_t=_j.load(open('towers.json'));X0=[]
for nm,pts in V.items():
    X0+=_t[nm]['base'];X0+=[30.0]*len(pts)
best=None
for FREEPP in (False,True):
  for yaw0 in np.radians([60,75,90,105,120]):
    for h in (80,120,180):
        s0=[0,-200,h,yaw0,-0.4,0,1500]+([W/2,H/2] if FREEPP else [])+[80,80,15,8]+X0
        try:s=least_squares(res,s0,max_nfev=4000)
        except Exception:continue
        rms=math.sqrt((s.fun**2).mean())
        if best is None or rms<best[0]-0.01 or (FREEPP and best[2]==False and rms<best[0]+0.3):best=(rms,s,FREEPP)
  FP=FREEPP
rms,s,FREEPP=best;p,q=unpack(s.x)
print('rms',round(rms,2),'freepp',FREEPP);print('cam',np.round(p,2));print('L1 L2 hg hb',np.round(q[:4],2))
print(np.round(s.fun.reshape(-1,2),1))
json.dump({'p':list(p),'q':list(q[:4]),'towers':list(q[4:])},open('cam.json','w'))
