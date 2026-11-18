import cv2,numpy as np,json,math,sys
# unwrap.py a0 a1 out : photo resampled on (angle, profile) of lower tier+walk+upper tier; x=0.05 deg/px
D=json.load(open('geo_build.json'));import os;p=json.load(open(os.environ.get('CAM','cam.json')))['p']
ph=cv2.imread(os.environ.get('PH','photo_clean.png'));Hi,Wi=ph.shape[:2]
RG=np.array(D['RG'])
def rg(a):f=(a%360)*4;i=int(f)%1440;t=f-int(f);return RG[i]*(1-t)+RG[(i+1)%1440]*t
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
Rm=R(*p[3:6])
a0,a1=float(sys.argv[1]),float(sys.argv[2]);out=sys.argv[3]
prof=json.loads(os.environ.get('PROF','[[1.5,1.0],[6.5,4.0],[8.5,4.0],[8.5,6.0],[18.0,12.7],[18.0,15.2]]'))
L=np.cumsum([0]+[math.hypot(prof[i+1][0]-prof[i][0],prof[i+1][1]-prof[i][1]) for i in range(len(prof)-1)])
S=np.arange(0,L[-1],0.1);A=np.arange(a0,a1,0.05)
mx=np.zeros((len(S),len(A)),np.float32);my=mx.copy()
for j,s in enumerate(S):
    k=min(np.searchsorted(L,s,side='right')-1,len(prof)-2);t=(s-L[k])/(L[k+1]-L[k])
    d=prof[k][0]+(prof[k+1][0]-prof[k][0])*t;z=prof[k][1]+(prof[k+1][1]-prof[k][1])*t
    r=np.array([rg(a) for a in A])+d;th=np.radians(A)
    X=np.c_[r*np.cos(th),r*np.sin(th),np.full(len(A),z)]
    dd=(X-p[:3])@Rm.T;mx[j]=Wi/2+p[6]*dd[:,0]/dd[:,2];my[j]=Hi/2-p[6]*dd[:,1]/dd[:,2]
im=cv2.remap(ph,mx,my,cv2.INTER_CUBIC);im=cv2.resize(im,(im.shape[1],im.shape[0]*3))
for i,a in enumerate(A):
    if abs(a-round(a))<0.026:
        cv2.line(im,(i,0),(i,6 if round(a)%5 else 14),(0,255,255),1)
        if round(a)%5==0:cv2.putText(im,str(round(a)),(i+2,24),0,0.4,(0,255,255),1)
cv2.imwrite(out,im)
