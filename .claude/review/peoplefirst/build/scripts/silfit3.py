# w0 camera from roof silhouette + field (grass) outline; plan from satellite (RG, rin/rout) is the truth
import cv2,numpy as np,json,sys
from scipy.optimize import minimize
camf,photof,outf=sys.argv[1:4]
Z=np.load('tris.npz');V,T,M=Z['V'],Z['T'],Z['M'];names=list(Z['names'])
RT=T[M==names.index('roof')];ph=cv2.imread(photof);Hi,Wi=ph.shape[:2]
D=json.load(open('geo_build.json'));RG=np.array(D['RG']);aa=np.radians(np.arange(0,360,0.5))
FG=np.c_[np.interp(np.degrees(aa)*4,np.arange(1440),RG)*np.cos(aa),np.interp(np.degrees(aa)*4,np.arange(1440),RG)*np.sin(aa),np.zeros_like(aa)]
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
def mask(p):
    uv=proj(p,V);m=np.zeros((Hi,Wi),np.uint8)
    cv2.fillPoly(m,[np.round(uv[t]*8).astype(np.int32) for t in RT],255,shift=3);return m
p0=np.array(json.load(open(camf))['p'])
hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV)
white=((hsv[...,2]>185)&(hsv[...,1]<40)).astype(np.uint8)*255
roi=cv2.dilate(mask(p0),np.ones((121,121),np.uint8));white=white&roi
white=cv2.morphologyEx(white,cv2.MORPH_OPEN,np.ones((3,3),np.uint8));white=cv2.morphologyEx(white,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(white);keep=[i for i in range(1,n) if st[i,4]>2500];white=(np.isin(lab,keep)*255).astype(np.uint8)
grass=((hsv[...,0]>28)&(hsv[...,0]<106)&(hsv[...,1]>60)&(hsv[...,2]>15)).astype(np.uint8)*255
grass=cv2.morphologyEx(grass,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
fr=np.zeros((Hi,Wi),np.uint8);cv2.fillPoly(fr,[np.round(proj(p0,FG)).astype(np.int32)],255);grass=grass&cv2.dilate(fr,np.ones((61,61),np.uint8))
c0=proj(p0,np.array([[0,0,0.0]]))[0].astype(int);n,lab,st,_=cv2.connectedComponentsWithStats(grass)
box=lab[c0[1]-40:c0[1]+40,c0[0]-40:c0[0]+40];vals,cnt=np.unique(box[box>0],return_counts=True);grass=((lab==vals[np.argmax(cnt)])*255).astype(np.uint8)
grass=cv2.morphologyEx(grass,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8));cs,_=cv2.findContours(grass,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);grass=np.zeros_like(grass);cv2.drawContours(grass,cs,-1,255,-1)
cv2.imwrite(outf+'_masks.png',np.dstack([grass,white,white*0]))
eP=cv2.Canny(white,50,150);dtP=cv2.distanceTransform(255-eP,cv2.DIST_L2,3)
eG=cv2.Canny(grass,50,150);dtG=cv2.distanceTransform(255-eG,cv2.DIST_L2,3)
S=np.array([20,20,20,0.005,0.005,0.005,50.0])
def parts(x):
    p=p0+x*S;m=mask(p);e=cv2.Canny(m,50,150);ys,xs=np.nonzero(e)
    a=np.minimum(dtP[ys,xs],40).mean();dtM=cv2.distanceTransform(255-e,cv2.DIST_L2,3);yy,xx=np.nonzero(eP);b=np.minimum(dtM[yy,xx],40).mean()
    uv=proj(p,FG);ok=(uv[:,0]>0)&(uv[:,0]<Wi-1)&(uv[:,1]>0)&(uv[:,1]<Hi-1);ui=uv[ok].astype(int);vis=m[ui[:,1],ui[:,0]]==0
    g=np.minimum(dtG[ui[vis,1],ui[vis,0]],40).mean() if vis.sum()>50 else 40
    return a+b,g
def cost(x):s,g=parts(x);return s+g
print('start',parts(np.zeros(7)),flush=True)
best=np.zeros(7)
for rnd in range(3):
    r=minimize(cost,best,method='Powell',options={'maxiter':4000,'xtol':1e-3,'ftol':1e-4});best=r.x;print('round',rnd,r.fun,parts(best),flush=True)
p=p0+best*S;json.dump({'p':list(map(float,p))},open(outf,'w'));print(list(map(float,p)))
