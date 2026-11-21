import numpy as np, cv2, math
W=[(30.98,-143.44,0),(30.78,-143.76,9.4),(33.72,-139.14,0),(33.61,-139.32,5.3),(36.57,-134.67,0),(36.37,-134.99,9.4),
   (34.06,-128.54,1.15),(33.50,-126.48,1.15),(33.02,-124.64,1.15),(32.70,-123.00,1.15)]
I=[(232,430),(210,245),(327,440),(312,302),(457,452),(437,180),(471,425),(506,427),(538,430),(570,432)]
W=np.array(W,float); I=np.array(I,float); best=None
for fov in range(35,80,1):
    f=300/math.tan(math.radians(fov/2)); K=np.array([[f,0,400],[0,f,300],[0,0,1.]])
    ok,r,t=cv2.solvePnP(W,I,K,None,flags=cv2.SOLVEPNP_ITERATIVE,useExtrinsicGuess=False) if False else cv2.solvePnP(W,I,K,None,flags=cv2.SOLVEPNP_SQPNP)
    P,_=cv2.projectPoints(W,r,t,K,None); e=np.sqrt(((P[:,0]-I)**2).sum(1)).mean()
    if best is None or e<best[0]: best=(e,fov,r,t,P)
e,fov,r,t,P=best; R,_=cv2.Rodrigues(r); C=(-R.T@t).ravel(); fwd=R.T@np.array([0,0,1.])
print('err px',round(e,1),'fov',fov,'eye',C.round(2),'target',(C+fwd*15).round(2))
print(np.c_[I,P[:,0].round(0)])
from scipy.optimize import least_squares
def proj(p):
    ex,ey,yaw,pit,fov=p; f=300/math.tan(math.radians(fov/2)); C=np.array([ex,ey,1.6])
    fw=np.array([math.cos(pit)*math.cos(yaw),math.cos(pit)*math.sin(yaw),math.sin(pit)]); rt=np.cross(fw,[0,0,1]); rt/=np.linalg.norm(rt); up=np.cross(rt,fw)
    d=W-C; x=d@rt; y=d@up; z=d@fw; return np.c_[400+f*x/z,300-f*y/z]
res=min((least_squares(lambda p:(proj(p)-I).ravel(),[ex,ey,math.atan2(-136-ey,32-ex),0.1,55],bounds=([0,-200,-7,-1,25],[90,-60,7,1,90])) for ex in (40,45,50,55) for ey in (-125,-118,-110,-100)),key=lambda r:r.cost)
p=res.x; e=np.sqrt(((proj(p)-I)**2).sum(1)); print('fixed z1.6: err',e.mean().round(1),'eye',p[:2].round(2),'yaw',round(math.degrees(p[2]),1),'pitch',round(math.degrees(p[3]),1),'fov',p[4].round(1))
print(np.c_[I,proj(p).round(0)])
fw=np.array([math.cos(p[3])*math.cos(p[2]),math.cos(p[3])*math.sin(p[2]),math.sin(p[3])]); print('target',(np.array([p[0],p[1],1.6])+fw*15).round(2))
