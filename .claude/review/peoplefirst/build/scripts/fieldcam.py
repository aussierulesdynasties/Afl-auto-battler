# camera refit on the field edge only: satellite field edge RG (z=0) pulled onto the photo's green-field boundary.
# optional k1 radial distortion (photo-side): python fieldcam.py cam.json out.json [k1]
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates
from refine_cam_R import R
camf,outf=sys.argv[1:3];K1=len(sys.argv)>3
p0=np.array(json.load(open(camf))['p']+[0.0]);ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2]
D=json.load(open('geo_sat.json'));RG=np.array(D['RG'])
A=np.arange(0,360,0.25);t=np.radians(A);X=np.c_[RG*np.cos(t),RG*np.sin(t),np.full(len(A),0.0)]
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;x=d[:,0]/d[:,2];y=d[:,1]/d[:,2];r2=(x*x+y*y);k=1+p[7]*r2*1e2
    return np.c_[Wi/2+p[6]*x*k,Hi/2-p[6]*y*k]
h=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV);m=((h[...,0]>30)&(h[...,0]<60)&(h[...,1]>60)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(m);g=(l==l[Hi//2+60,Wi//2]).astype(np.uint8)
g=cv2.morphologyEx(g,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))   # fill posts/marks
b=cv2.morphologyEx(g,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
dg=cv2.distanceTransform((~b).astype(np.uint8),cv2.DIST_L2,5)
# visible: the field edge is not under a roof: the photo pixel just outside the edge (d=+3 m, z=1) is not white roof
uv=proj(p0,X);uo=proj(p0,np.c_[(RG+3)*np.cos(t),(RG+3)*np.sin(t),np.full(len(A),1.0)])
hv=h[np.clip(uo[:,1].astype(int),0,Hi-1),np.clip(uo[:,0].astype(int),0,Wi-1)]
vis=(dg[np.clip(uv[:,1].astype(int),0,Hi-1),np.clip(uv[:,0].astype(int),0,Wi-1)]<30)&~((hv[:,2]>215)&(hv[:,1]<30))
Xv=X[vis];Av=A[vis];print('visible pts',vis.sum())
def res(p):
    a=proj(p,Xv);return map_coordinates(dg,[a[:,1],a[:,0]],order=1,mode='nearest')
s=np.array([20,20,20,0.002,0.002,0.002,50.0,0.01 if K1 else 0])
r0=res(p0);fit=least_squares(lambda q:res(p0+q*s),np.zeros(8),loss='soft_l1',f_scale=2,diff_step=0.05)
p=p0+fit.x*s;r1=res(p)
for lo in range(0,360,30):
    k=(Av>=lo)&(Av<lo+30)
    if k.sum():print(f'{lo:3d}-{lo+30:3d} n={k.sum():3d} before {np.median(r0[k]):5.1f} after {np.median(r1[k]):5.1f}')
print('all before',np.median(r0).round(2),'after',np.median(r1).round(2),'delta',np.round(p-p0,4))
json.dump({'p':list(map(float,p[:7])),'k1':float(p[7])},open(outf,'w',newline=''))
cv2.imwrite('fc_mask.png',b.astype(np.uint8)*255)
