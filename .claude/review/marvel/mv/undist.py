import sys,numpy as np
from PIL import Image
from cam2 import dis
src,dst,sc=sys.argv[1],sys.argv[2],float(sys.argv[3])
im=np.asarray(Image.open(src).convert('RGB')).astype(np.float32);H,W=im.shape[:2]
ys,xs=np.mgrid[0:H,0:W];uv=np.stack([(xs.ravel()+0.5)/sc,(ys.ravel()+0.5)/sc],1)
s=dis(uv)*sc-0.5;x=np.clip(s[:,0],0,W-1.001);y=np.clip(s[:,1],0,H-1.001)
x0=x.astype(int);y0=y.astype(int);fx=(x-x0)[:,None];fy=(y-y0)[:,None]
o=(im[y0,x0]*(1-fx)*(1-fy)+im[y0,x0+1]*fx*(1-fy)+im[y0+1,x0]*(1-fx)*fy+im[y0+1,x0+1]*fx*fy)
Image.fromarray(o.reshape(H,W,3).clip(0,255).astype(np.uint8)).save(dst)
