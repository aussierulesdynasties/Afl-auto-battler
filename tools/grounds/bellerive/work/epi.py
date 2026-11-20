# python work/epi.py v1 u v v2 out [x0,y0,x1,y1] : ray through pixel (u,v) of v1 drawn into v2 with ticks every 1 m of depth-height (labels = z)
import sys,cv2,numpy as np;sys.path.insert(0,'work');import tri as T,earthcam as E
v1,u,w,v2,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5]
o,d=T.ray(v1,u,w);c=T.camv(v2);im=cv2.imread(f'ge/{v2}.png')
pts=[];zs=[]
for z in np.arange(-2,30.01,0.25):
  s=(z-o[2])/d[2];X=o+s*d;pts.append(E.proj(c,X));zs.append(z)
P=np.array(pts,np.int32);cv2.polylines(im,[P],False,(0,0,255),1)
for p,z in zip(pts,zs):
  if abs(z-round(z))<1e-6:
    q=tuple(np.int32(p));cv2.circle(im,q,2,(0,255,255),-1)
    if int(round(z))%2==0:cv2.putText(im,str(int(round(z))),(q[0]+5,q[1]),0,0.35,(0,255,255),1)
if len(sys.argv)>6:
  x0,y0,x1,y1=map(int,sys.argv[6].split(','));im=im[y0:y1,x0:x1];im=cv2.resize(im,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
cv2.imwrite(out,im)
s=(np.array([6,10,14])-o[2])/d[2];print([np.round(o+k*d,1).tolist() for k in s])
