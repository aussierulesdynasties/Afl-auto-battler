import cv2,numpy as np,json,sys
camf,out=sys.argv[1:3];tr=sys.argv[3] if len(sys.argv)>3 else 'tris.npz'
Z=np.load(tr);V,T,M=Z['V'],Z['T'],Z['M'];names=list(Z['names'])
ph=cv2.imread('w0_clean.png');Hi,Wi=ph.shape[:2]
def R(yaw,p_,roll):
    cy,sy,cp,sp,cr,sr=np.cos(yaw),np.sin(yaw),np.cos(p_),np.sin(p_),np.cos(roll),np.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f);return np.array([cr*r+sr*u,-sr*r+cr*u,f])
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
p=json.load(open(camf))['p'];uv=proj(p,V);ov=ph.copy()
for nm,col in (('roof',(0,0,255)),('screen',(255,0,255)),('stripes',(255,255,0)),('seats',(0,255,0)),('tower',(0,255,255)),('fence',(255,128,0))):
    m=np.zeros((Hi,Wi),np.uint8);cv2.fillPoly(m,[np.round(uv[t]*8).astype(np.int32) for t in T[M==names.index(nm)]],255,shift=3)
    ov[cv2.Canny(m,50,150)>0]=col
cv2.imwrite(out,ov)
