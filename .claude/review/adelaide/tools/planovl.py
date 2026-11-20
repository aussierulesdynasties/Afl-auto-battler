import sys, numpy as np, cv2
sys.path.insert(0,'tools')
from esri import m2px
from planreg import m2pl
page=sys.argv[1]; x0,x1,y0,y1=map(int,sys.argv[2:6]); S=float(sys.argv[6]); out=sys.argv[7]
lean=float(sys.argv[8]) if len(sys.argv)>8 else 0.0   # metres height: shift plan to roof-top lean
mos=cv2.imread('esri/mosaic.jpg'); pl=cv2.imread('hplans/%s.png'%page,0)
W=int((x1-x0)*S); H=int((y1-y0)*S)
xs,ys=np.meshgrid(x0+np.arange(W)/S, y0+np.arange(H)/S)
xs=xs-0.82*lean; ys=ys-0.26*lean
a0=np.array(m2px(0,0)); ax=np.array(m2px(1,0))-a0; ay=np.array(m2px(0,1))-a0; J=np.linalg.inv(np.c_[ax,ay])
d=np.stack([xs-a0[0],ys-a0[1]],-1)@J.T; u,v=m2pl(d[...,0],d[...,1])
warp=cv2.remap(pl,u.astype(np.float32),v.astype(np.float32),cv2.INTER_LINEAR,borderValue=255)
bg=cv2.resize(mos[y0:y1,x0:x1],(W,H),interpolation=cv2.INTER_CUBIC)
import os; m=warp<int(os.environ.get("TH","140")); o=bg.copy(); o[m]=(0,0,255)
for gx in range(x0-x0%20,x1,20):
    X=int((gx-x0)*S); cv2.line(o,(X,0),(X,8),(0,255,255),1); cv2.putText(o,str(gx),(X+2,18),0,0.35,(0,255,255),1)
for gy in range(y0-y0%20,y1,20):
    Y=int((gy-y0)*S); cv2.line(o,(0,Y),(8,Y),(0,255,255),1); cv2.putText(o,str(gy),(10,Y+4),0,0.35,(0,255,255),1)
cv2.imwrite(out,o)
