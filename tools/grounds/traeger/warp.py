import json,sys,math,numpy as np
from PIL import Image
from cam import *
import f2w as F
if len(sys.argv)>2:F._s[:]=[math.radians(float(sys.argv[2])),float(sys.argv[3]),float(sys.argv[4])]
p=load();J=json.load(open('sat/sat.json'));sat=np.asarray(Image.open('sat/sat.png').convert('RGB'))
ox=(J['cx']-J['x0'])*256;oy=(J['cy']-J['y0'])*256;m=J['mpp']
ref=np.asarray(Image.open('refs/ref.jpg').convert('RGB')).astype(float)
H,W=ref.shape[:2];vv,uu=np.mgrid[0:H,0:W]
M=R(*p[3:6]);d=np.stack([(uu-p[7])/p[6],-(vv-p[8])/p[6],np.ones_like(uu,float)],-1)@M
t=-p[2]/d[...,2];X=p[0]+t*d[...,0];Y=p[1]+t*d[...,1]
Wd=F.f2w(np.stack([X.ravel(),Y.ravel()],1));sx=(ox+Wd[:,0]/m).reshape(H,W);sy=(oy-Wd[:,1]/m).reshape(H,W)
ok=(t>0)&(sx>=0)&(sy>=0)&(sx<sat.shape[1]-1)&(sy<sat.shape[0]-1)
out=ref.copy();s=sat[np.clip(sy.astype(int),0,sat.shape[0]-1),np.clip(sx.astype(int),0,sat.shape[1]-1)].astype(float)
out[ok]=0.45*ref[ok]+0.55*s[ok]
Image.fromarray(out.astype(np.uint8)).save(sys.argv[1])
