import json,numpy as np,cv2,math,sys
from scipy.optimize import least_squares
import stand;stand.build();B=stand.B;W=stand.W
T=json.load(open('towers.json'));w,h=3840,2880
ring=[p for p in json.load(open('prims.json')) if p['name']=='fence_ring'][0]['pts']
R3=[];n=len(ring)
for i in range(n):
    a,b=np.array(ring[i]),np.array(ring[(i+1)%n])
    for t in np.linspace(0,1,6,endpoint=False):R3.append(list(a+(b-a)*t)+[1.0])
R3=np.array(R3)
P=[];U=[]
for k,uv in zip(range(3,8),[(2522,818),(2640,1012),(2727,1153),(2790,1258),(2842,1335)]):P.append(W(k*B,-0.4,11.09));U.append(uv)
for z,v in ((10.75,948),(7.3,1300)):P.append(W(7.9,4.0,z));U.append((1790,v))
for nm,pts in (('FL_pole',[(3600,2000,0),(3592,745,'hbot')]),('FL_2',[(3317,2040,0),(3312,1002,'hbot')])):
    for u,v,z in pts:P.append(T[nm]['base']+[0 if z==0 else T[nm][z]]);U.append((u,v))
for (s_,t_,z_),uv in (((7.75,4.15,9.62),(1772,1045)),((6.3,5.6,9.62),(1545,1050)),((7.75,4.15,8.12),(1772,1212)),((6.3,5.6,8.12),(1545,1215))):P.append(W(s_,t_,z_));U.append(uv)
SEL=[0,1,5,6,11,12,13,14];P=np.array(P,float)[SEL];U=np.array(U,float)[SEL]
FU=np.array([(2340,2110),(2290,2160),(2240,2230),(2205,2300),(2180,2400),(2165,2500),(2155,2600),(2150,2700),(2150,2800)],float)
def K(f):return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
def Rm(yaw,pitch,roll):
    f=np.array([math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch)])
    r=np.cross(f,[0,0,1]);r/=np.linalg.norm(r);d=np.cross(f,r)
    c,s=math.cos(roll),math.sin(roll);r2=c*r+s*d;d2=-s*r+c*d
    return np.array([r2,d2,f])
def proj(q,X):
    C=q[0:3];R=Rm(*q[3:6]);Xc=(X-C)@R.T;z=Xc[:,2];x=Xc[:,0]/z;y=Xc[:,1]/z;r2=(x*x+y*y)*(q[6]/w)**2*4;d=1+q[7]*r2
    return np.c_[q[6]*x*d+w/2,q[6]*y*d+h/2],z
def rs(q):
    up,_=proj(q,P);e=(up-U).ravel()
    fr,z=proj(q,R3);fr=fr[z>1]
    if len(fr)<2:fe=np.full(len(FU),500.)
    else:
        # distance from each fence pick to the projected polyline (point-to-point on dense ring is fine)
        fe=np.array([np.min(np.linalg.norm(fr-u,axis=1)) for u in FU])
    return np.r_[e,0.3*fe,20*(q[2]-1.6),0.05*(q[6]-2750),30*q[7]]
best=None
for cx in range(-70,10,10):
  for cy in range(-110,-20,10):
    C=np.array([cx,cy,1.6]);d=np.array([-82,5])-C[:2];yaw=math.atan2(d[1],d[0])
    for dy in (-0.3,0,0.3):
      try:s=least_squares(rs,np.r_[C,yaw+dy,0.15,0,2750,0.0],max_nfev=300)
      except Exception:continue
      if best is None or s.cost<best.cost:best=s
q=best.x;r=rs(q);print('q',np.round(q,3),'pts',np.round(np.linalg.norm(r[:2*len(P)].reshape(-1,2),axis=1)),'fence',np.round(r[2*len(P):2*len(P)+len(FU)]))
R=Rm(*q[3:6]);rv=cv2.Rodrigues(R)[0].ravel();json.dump(dict(k1=q[7],f=q[6],r=rv.tolist(),t=(-R@q[:3]).tolist(),w=w,h=h),open('cam_c06f.json','w'))
