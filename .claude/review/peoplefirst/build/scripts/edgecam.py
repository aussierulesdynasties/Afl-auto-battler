# camera refit on edges: 3D points on the model's white-roof boundary and field-hole boundary (from the position render)
# are pulled onto the same boundaries in the photo (distance transforms). python edgecam.py cam.json pos.npy render.png out.json
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates
camf,posf,renf,outf=sys.argv[1:5]
p0=np.array(json.load(open(camf))['p']);P=np.load(posf);ren=cv2.imread(renf,cv2.IMREAD_UNCHANGED);ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2]
from refine_cam_R import R
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
def white(im):
    h=cv2.cvtColor(im[...,:3],cv2.COLOR_BGR2HSV);m=((h[...,2]>215)&(h[...,1]<28)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8));n,l,st,_=cv2.connectedComponentsWithStats(m)
    big=[i for i in range(1,n) if st[i,4]>20000];return np.isin(l,big).astype(np.uint8)
def green(im):
    h=cv2.cvtColor(im[...,:3],cv2.COLOR_BGR2HSV);m=((h[...,0]>30)&(h[...,0]<60)&(h[...,1]>60)).astype(np.uint8)
    n,l,st,_=cv2.connectedComponentsWithStats(cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8)))
    c=l[Hi//2+60,Wi//2];return (l==c).astype(np.uint8)
def bnd(m):return (cv2.morphologyEx(m,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0)
pw=bnd(white(ph));pg=bnd(green(ph))
hole=((ren[...,3]<10)).astype(np.uint8);n,l,st,_=cv2.connectedComponentsWithStats(hole);hole=(l==l[Hi//2+60,Wi//2]).astype(np.uint8)
rw=bnd(white(ren))&(ren[...,3]>200);rg=bnd(hole)&(ren[...,3]>200)
cv2.imwrite('ec_masks.png',np.dstack([pw*255,pg*255,(rw|rg)*255]).astype(np.uint8))
dw=cv2.distanceTransform((~pw).astype(np.uint8),cv2.DIST_L2,5);dg=cv2.distanceTransform((~pg).astype(np.uint8),cv2.DIST_L2,5)
def pts(m,k):
    ys,xs=np.where(m);X=P[ys,xs];ok=~np.isnan(X[:,0]);X=X[ok];r=np.random.default_rng(1);return X[r.choice(len(X),min(k,len(X)),replace=False)]
XW=pts(rw,4000);XG=pts(rg,2000)
def res(p):
    a=proj(p,XW);b=proj(p,XG)
    ew=map_coordinates(dw,[a[:,1],a[:,0]],order=1,mode='nearest');eg=map_coordinates(dg,[b[:,1],b[:,0]],order=1,mode='nearest')
    return np.r_[ew,eg]
s=np.array([20,20,20,0.002,0.002,0.002,50.0])
r0=res(p0);print('before median white',np.median(r0[:len(XW)]).round(2),'field',np.median(r0[len(XW):]).round(2))
fit=least_squares(lambda q:res(p0+q*s),np.zeros(7),loss='soft_l1',f_scale=3,diff_step=0.05)
p=p0+fit.x*s;r1=res(p);print('after  median white',np.median(r1[:len(XW)]).round(2),'field',np.median(r1[len(XW):]).round(2))
print('delta',np.round(p-p0,4));json.dump({'p':list(map(float,p))},open(outf,'w',newline=''))
