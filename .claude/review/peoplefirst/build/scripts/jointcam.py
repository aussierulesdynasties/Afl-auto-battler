# joint refit: camera (7) + roof edge heights hin/hout (3 coeffs each). Plan is fixed (satellite RG, rin, rout, roofshift).
# field edge -> photo green boundary; roof outer edge and navy/white line -> photo white-roof boundary.
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates
from refine_cam_R import R
outc,outg=sys.argv[1:3]
p0=np.array(json.load(open('cam_old.json'))['p']);ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2]
D=json.load(open('geo_sat.json'));RG=np.array(D['RG']);RI=np.array(D['rin']);RO=np.array(D['rout']);DZ=np.array(D['hout_dz']);SH=D['roofshift']
A=np.arange(0,360,0.25);t=np.radians(A);c,s=np.cos(t),np.sin(t);A0,A1=D['a0'],D['a1']
roof=((A>=A0)|(A<=A1-360))
def cf(k,i=None):return k[0]+k[1]*c+k[2]*s
def proj(p,X):
    d=(X-p[:3])@R(*p[3:6]).T;return np.c_[Wi/2+p[6]*d[:,0]/d[:,2],Hi/2-p[6]*d[:,1]/d[:,2]]
hsv=cv2.cvtColor(ph,cv2.COLOR_BGR2HSV)
g=((hsv[...,0]>30)&(hsv[...,0]<60)&(hsv[...,1]>60)).astype(np.uint8)
g=cv2.morphologyEx(cv2.morphologyEx(g,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(g);g=cv2.morphologyEx((l==l[Hi//2+60,Wi//2]).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
w=((hsv[...,2]>215)&(hsv[...,1]<28)).astype(np.uint8);w=cv2.morphologyEx(w,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,l,st,_=cv2.connectedComponentsWithStats(w);w=np.isin(l,[i for i in range(1,n) if st[i,4]>20000]).astype(np.uint8)
bd=lambda m:cv2.morphologyEx(m,cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0
dg=cv2.distanceTransform((~bd(g)).astype(np.uint8),cv2.DIST_L2,5);dw=cv2.distanceTransform((~bd(w)).astype(np.uint8),cv2.DIST_L2,5)
def pts(q):
    hin=np.array(D['hin'])+q[7:10];hout=np.array(D['hout'])+q[10:13]
    XF=np.c_[RG*c,RG*s,0*A]
    XO=np.c_[RO*c+SH[0],RO*s+SH[1],cf(hout)+DZ]
    ri=RI+0.6;XI=np.c_[ri*c+SH[0],ri*s+SH[1],cf(hin)+0.3+(cf(hout)-cf(hin))*(5.0/(RO-RI+5))]
    return XF,XO,XI
def samp(dt,uv):return map_coordinates(dt,[uv[:,1],uv[:,0]],order=1,mode='nearest')
q0=np.r_[p0,np.zeros(6)];XF,XO,XI=pts(q0)
uo=proj(p0,np.c_[(RG+3)*c,(RG+3)*s,np.ones(len(A))]);hv=hsv[np.clip(uo[:,1].astype(int),0,Hi-1),np.clip(uo[:,0].astype(int),0,Wi-1)]
vF=(samp(dg,proj(p0,XF))<30)&~((hv[:,2]>215)&(hv[:,1]<30))
vO=roof&(samp(dw,proj(p0,XO))<15);vI=roof&(samp(dw,proj(p0,XI))<15)
print('pts field',vF.sum(),'outer',vO.sum(),'inner',vI.sum())
def res(q):
    XF,XO,XI=pts(q);return np.r_[samp(dg,proj(q,XF[vF])),samp(dw,proj(q,XO[vO])),samp(dw,proj(q,XI[vI]))]
sc=np.r_[20,20,20,0.002,0.002,0.002,50.0,[0.5]*6]
r0=res(q0);fit=least_squares(lambda x:res(q0+x*sc),np.zeros(13),loss='soft_l1',f_scale=2,diff_step=0.05)
q=q0+fit.x*sc;r1=res(q);nF,nO=vF.sum(),vO.sum()
for nm,sl in (('field',slice(0,nF)),('outer',slice(nF,nF+nO)),('inner',slice(nF+nO,None))):
    print(nm,'before',np.median(r0[sl]).round(2),'after',np.median(r1[sl]).round(2),'p90',np.percentile(r1[sl],90).round(1))
print('cam delta',np.round(q[:7]-p0,4),'hin',np.round(np.array(D['hin'])+q[7:10],2),'hout',np.round(np.array(D['hout'])+q[10:13],2))
json.dump({'p':list(map(float,q[:7]))},open(outc,'w',newline=''))
D['hin']=list(map(float,np.round(np.array(D['hin'])+q[7:10],3)));D['hout']=list(map(float,np.round(np.array(D['hout'])+q[10:13],3)))
json.dump(D,open(outg,'w',newline=''))
