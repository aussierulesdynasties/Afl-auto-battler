# refine a camera: SIFT-match RENDER (textured model through CAM) to PHOTO, lift matches to 3D with the position render, robust fit
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
camf,posf,renf,photof,outf=sys.argv[1:6]
p0=np.array(json.load(open(camf))['p']);P=np.load(posf);ren=cv2.imread(renf,cv2.IMREAD_UNCHANGED);ph=cv2.imread(photof)
Hi,Wi=ph.shape[:2]
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
# sanity: position render reprojects to its own pixel
ys,xs=np.where(~np.isnan(P[...,0]));k=np.random.default_rng(0).choice(len(xs),2000);e=proj(p0,P[ys[k],xs[k]])-np.c_[xs[k]+0.5,ys[k]+0.5]
print('pos-render self consistency px',np.round(np.median(np.abs(e),0),2))
g1=cv2.cvtColor(ren[...,:3],cv2.COLOR_BGR2GRAY);m1=(ren[...,3]>200).astype(np.uint8)*255;g2=cv2.cvtColor(ph,cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(20000);k1,d1=sift.detectAndCompute(g1,m1);k2,d2=sift.detectAndCompute(g2,None)
mt=cv2.BFMatcher().knnMatch(d1,d2,k=2);good=[a for a,b in mt if a.distance<0.8*b.distance]
A=np.array([k1[g.queryIdx].pt for g in good]);B=np.array([k2[g.trainIdx].pt for g in good])
near=np.linalg.norm(A-B,axis=1)<float(sys.argv[6]) if len(sys.argv)>6 else np.ones(len(A),bool)
A,B=A[near],B[near];X=P[A[:,1].astype(int),A[:,0].astype(int)];ok=~np.isnan(X[:,0]);X,B=X[ok],B[ok]
print('matches',len(good),'near',near.sum(),'3d',len(X))
p=p0.copy();inl=np.ones(len(X),bool)
for it in range(6):
    r=least_squares(lambda q:(proj(q,X[inl])-B[inl]).ravel(),p,loss='soft_l1',f_scale=3)
    p=r.x;res=np.linalg.norm(proj(p,X)-B,axis=1);thr=max(3,np.percentile(res,60)*2.5) if it<3 else 4
    inl=res<thr;print(it,'inliers',inl.sum(),'median',round(float(np.median(res[inl])),2),'rms',round(float(np.sqrt((res[inl]**2).mean())),2))
json.dump({'p':list(map(float,p))},open(outf,'w'));print(list(map(float,p)))
