# Model as the survey camera sees it on the ground plane: each top-surface point at height h moves to C + (P-C)*Hc/(Hc-h).
import numpy as np,cv2,sys
from PIL import Image
r_top,znpy,out=sys.argv[1],sys.argv[2],sys.argv[3];Cx,Cy,Hc=map(float,sys.argv[4:7]);H=float(sys.argv[7]);mpp=0.25
M=np.asarray(Image.open(r_top).convert('RGBA'));n=M.shape[0]
Z=np.load(znpy);Z=cv2.resize(np.nan_to_num(Z,nan=0),(n,n),interpolation=cv2.INTER_NEAREST)
jj,ii=np.nonzero(M[...,3]>10);h=Z[jj,ii]
x=-H+(ii+0.5)*mpp;y=H-(jj+0.5)*mpp;k=Hc/(Hc-h)
xs=Cx+(x-Cx)*k;ys=Cy+(y-Cy)*k
I=np.round((xs+H)/mpp-0.5).astype(int);J=np.round((H-ys)/mpp-0.5).astype(int)
o=np.argsort(h);O=np.zeros_like(M);ok=(I>=0)&(I<n)&(J>=0)&(J<n)
for idx in (o[ok[o]],):O[J[idx],I[idx]]=M[jj[idx],ii[idx]]
# close 1-px holes
a=O[...,3]>0;fill=cv2.dilate(O,np.ones((3,3),np.uint8));hole=(~a)&(cv2.erode(cv2.dilate(a.astype(np.uint8),np.ones((3,3),np.uint8)),np.ones((3,3),np.uint8))>0)
O[hole]=fill[hole];Image.fromarray(O).save(out);print('max shift m',float(np.max(np.hypot(xs-x,ys-y))))
