# silhouette (roof) + tower-point fit, unmirrored w0
import cv2,numpy as np,json,sys
exec(open('silfit.py').read().split("p0=np.array")[0].split("camf,photof,outf")[0])
camf,photof,outf=sys.argv[1:4]
Z=np.load('tris.npz');V,T,M=Z['V'],Z['T'],Z['M'];names=list(Z['names'])
RT=T[M==names.index('roof')];ph=cv2.imread(photof);Hi,Wi=ph.shape[:2]
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
def mask(p):
    uv=proj(p,V);m=np.zeros((Hi,Wi),np.uint8)
    cv2.fillPoly(m,[np.round(uv[t]*8).astype(np.int32) for t in RT],255,shift=3);return m
TW=np.array(json.load(open('geo_build.json'))['towers'])
heads=[[527,357],[1047,295],[1411,450],[447,590],[799,805],[1427,690]];bases=[None,None,None,[452,847],None,[1416,955]]
perm=[3,5,4,1,0,2];X=[];U=[]
for i,k in enumerate(perm):
    X.append([TW[k,0],TW[k,1],TW[k,2]-5.5]);U.append(heads[i])
    if bases[i]:X.append([TW[k,0],TW[k,1],0]);U.append(bases[i])
X=np.array(X);U=np.array(U,float)
p0=np.array(json.load(open(camf))['p'])
hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV);white=((hsv[...,2]>185)&(hsv[...,1]<40)).astype(np.uint8)*255
roi=cv2.dilate(mask(p0),np.ones((81,81),np.uint8));white=white&roi
white=cv2.morphologyEx(white,cv2.MORPH_OPEN,np.ones((3,3),np.uint8));white=cv2.morphologyEx(white,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
n,lab,st,_=cv2.connectedComponentsWithStats(white);k=1+np.argmax(st[1:,4]);white=((lab==k)*255).astype(np.uint8)
cv2.imwrite(outf+'_photomask.png',white)
eP=cv2.Canny(white,50,150);dtP=cv2.distanceTransform(255-eP,cv2.DIST_L2,3)
S=np.array([20,20,20,0.005,0.005,0.005,50.0])
def parts(x):
    p=p0+x*S;m=mask(p);e=cv2.Canny(m,50,150);ys,xs=np.nonzero(e)
    a=np.minimum(dtP[ys,xs],40).mean();dtM=cv2.distanceTransform(255-e,cv2.DIST_L2,3);yy,xx=np.nonzero(eP);b=np.minimum(dtM[yy,xx],40).mean()
    t=np.sqrt(((proj(p,X)-U)**2).sum(1).mean());return a+b,t
def cost(x):
    s,t=parts(x);return s+0.5*t
print('start',parts(np.zeros(7)))
best=np.zeros(7)
for rnd in range(3):
    r=minimize(cost,best,method='Powell',options={'maxiter':4000,'xtol':1e-3,'ftol':1e-4});best=r.x;print('round',rnd,r.fun,parts(best),flush=True)
p=p0+best*S;json.dump({'p':list(map(float,p))},open(outf,'w'));print(list(map(float,p)))
m=mask(p);ov=ph.copy();ov[cv2.Canny(m,50,150)>0]=(0,0,255);ov[eP>0]=(0,255,0)
for q in proj(p,X):cv2.circle(ov,tuple(int(v) for v in q),6,(255,0,255),2)
for q in U:cv2.circle(ov,tuple(int(v) for v in q),3,(0,255,255),-1)
cv2.imwrite(outf+'_ov.jpg',ov)
