# 1985 night aerial: camera solved from the six light-tower heads and four shaft lines (towers vertical, z from turf).
import cv2,numpy as np,json
from scipy.optimize import least_squares
T={'T1':(-116,83.4),'T2':(6,141.1),'T3':(127.9,63),'T4':(121.1,-74),'T5':(-3.7,-133.2),'T6':(-123.9,-51.1)}
ZB,ZH=4.2,84.2
heads={'T5':(349,520),'T6':(682,538),'T4':(150,572),'T1':(838,612),'T3':(266,678),'T2':(653,697)}
shafts={'T5':[(348,545),(348,645)],'T6':(None),'T4':[(141,600),(138.5,720)],'T1':[(836,645),(838,785)]}
shafts['T6']=[(684,555),(684,650)]
W,H=965,1200
def proj(p,X):
    rv,tv,f=p[:3],p[3:6],p[6]; K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1]])
    pr,_=cv2.projectPoints(np.array(X,float),rv,tv,K,None); return pr[:,0]
def res(p):
    r=[]
    for n,(u,v) in heads.items(): q=proj(p,[(T[n][0],T[n][1],ZH)])[0]; r+= [q[0]-u,q[1]-v]
    for n,pts in shafts.items():
        a,b=proj(p,[(T[n][0],T[n][1],ZB),(T[n][0],T[n][1],ZH)]); d=(b-a)/np.linalg.norm(b-a); nrm=np.array([-d[1],d[0]])
        for u,v in pts: r.append(np.dot(np.array([u,v])-a,nrm))
    return np.array(r)
if __name__=='__main__':
    obj=np.array([(T[n][0],T[n][1],ZH) for n in heads]); img=np.array(list(heads.values()),float)
    best=None
    for f in [2000,2500,3000,3500,4000,5000,6000]:
        K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1]]); ok,rv,tv=cv2.solvePnP(obj,img,K,None,flags=cv2.SOLVEPNP_SQPNP)
        s=least_squares(res,np.r_[rv.ravel(),tv.ravel(),f])
        if best is None or s.cost<best.cost: best=s
    p=best.x; r=res(p); R,_=cv2.Rodrigues(p[:3]); C=-R.T@p[3:6]
    print('f %.0f camera %s rms %.2f px'%(p[6],C.round(1),np.sqrt(np.mean(r**2)))); print(np.round(r,1))
    json.dump({'p':p.tolist()},open('cam85.json','w'))
