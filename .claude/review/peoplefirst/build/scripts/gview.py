import cv2,numpy as np,json,sys
from gpaint_cam import R
g=cv2.imread(sys.argv[1] if len(sys.argv)>1 else 'htex/ground.png');M=g.shape[0]
ph=cv2.imread('photo_clean.png');Hi,Wi=ph.shape[:2];p=json.load(open('cam.json'))['p']
Rm=R(*p[3:6]);u,v=np.meshgrid(np.arange(Wi)+0.5,np.arange(Hi)+0.5)
dc=np.stack([(u-Wi/2)/p[6],-(v-Hi/2)/p[6],np.ones_like(u)],-1)@Rm
t=-p[2]/dc[...,2];X=p[0]+t*dc[...,0];Y=p[1]+t*dc[...,1]
mx=((X+200)/400*M).astype(np.float32);my=((200-Y)/400*M).astype(np.float32)
s=cv2.remap(g,mx,my,cv2.INTER_LINEAR,borderValue=(0,0,0));s[(t<0)|(np.abs(X)>200)|(np.abs(Y)>200)]=0
cv2.imwrite('gview.jpg',np.vstack([ph,s]),[cv2.IMWRITE_JPEG_QUALITY,85])
