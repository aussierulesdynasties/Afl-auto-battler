# Perspective-rectify one planar face from a photo.
# python rect.py src "TLx,TLy TRx,TRy BRx,BRy BLx,BLy" width_m height_m px_per_m out [upscale_src]
import sys,numpy as np
from PIL import Image
src,q,wm,hm,ppm,out=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
Q=[tuple(map(float,p.split(','))) for p in q.split()]
W,H=max(1,round(wm*ppm)),max(1,round(hm*ppm))
D=[(0,0),(W,0),(W,H),(0,H)]
A=[];B=[]
for (x,y),(u,v) in zip(D,Q):   # output (x,y) -> input (u,v)
    A.append([x,y,1,0,0,0,-u*x,-u*y]);B.append(u);A.append([0,0,0,x,y,1,-v*x,-v*y]);B.append(v)
c=np.linalg.solve(np.array(A,float),np.array(B,float))
im=Image.open(src).convert('RGB')
im.transform((W,H),Image.PERSPECTIVE,tuple(c),Image.BICUBIC).save(out);print(out,W,H)
