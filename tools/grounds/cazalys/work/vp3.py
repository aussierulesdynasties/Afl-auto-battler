import numpy as np, math
from scipy.optimize import least_squares
PB=np.array([(1106,1089)],float)  # R post base (full res)
BT=np.array([(1132,1022.5),(1216,1027.5),(1294,1034),(1368,1040),(1442,1048.5)],float)
BB=np.array([(1132,1098.5),(1216,1109),(1294,1121.5),(1368,1135),(1442,1150)],float)
A=np.array([3.9,12.6]); A/=np.linalg.norm(A); N=np.array([A[1],-A[0]])
def proj(c,W):
    f,ex,ey,eh,yaw,cy=c; E=np.array([ex,ey,eh]); fw=np.array([math.cos(yaw),math.sin(yaw),0]); rt=np.array([fw[1],-fw[0],0]); up=np.array([0,0,1.])
    d=W-E; z=d@fw; return np.c_[960+f*(d@rt)/z, cy-f*(d@up)/z]
def world(q):
    s0,sp,py=q; base=np.array([35.7,-123.6])+N*3.0
    B=[(*(base+A*(s0+sp*k)),0.15) for k in range(5)]; T=[(x,y,1.15) for x,y,_ in B]
    return np.array(B),np.array(T),np.array([(36.3,py,0.0)])
def res(p):
    B,T,P=world(p[6:]); c=p[:6]
    return np.concatenate([(proj(c,B)-BB).ravel(),(proj(c,T)-BT).ravel(),(proj(c,P)-PB).ravel()])
best=None
for f in (900,1300,1800):
  for ex,ey in ((45,-125),(48,-118),(42,-128)):
    yaw=math.atan2(-134-ey,34-ex)
    r=least_squares(res,[f,ex,ey,1.7,yaw,900,-5,2,-130.5],bounds=([400,20,-160,1.5,-10,400,-20,0.8,-140],[4000,90,-90,1.75,10,1440,10,4,-125]))
    if best is None or r.cost<best.cost: best=r
p=best.x; e=np.abs(res(p)).reshape(-1,2); print('px err max',e.max().round(1),'mean',e.mean().round(1))
f,ex,ey,eh,yaw,cy=p[:6]; print('f %.0f (vfov %.1f) eye %.2f,%.2f,%.2f yaw %.1f cy %.0f'%(f,2*math.degrees(math.atan(720/f)),ex,ey,eh,math.degrees(yaw),cy)); print('bollard start s %.2f spacing %.2f  Rpost y %.2f'%tuple(p[6:]))
