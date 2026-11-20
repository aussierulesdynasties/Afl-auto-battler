# python work/ruler.py view out x0,y0,x1,y1 "b,r[,ztop]" ... : vertical height rulers (ticks every 2 m, long every 10) at polar points, crop box in px
import sys,math,cv2,numpy as np;sys.path.insert(0,'work');import tri as T,earthcam as E
v,out=sys.argv[1],sys.argv[2];x0,y0,x1,y1=map(int,sys.argv[3].split(','));im=cv2.imread(f'ge/{v}.png');c=T.camv(v)
C=[(255,0,255),(0,255,255),(0,128,255),(0,255,0),(255,255,0),(0,0,255)]
for k,a in enumerate(sys.argv[4:]):
  f=[float(q) for q in a.split(',')];b,r=f[0],f[1];zt=f[2] if len(f)>2 else 40;col=C[k%6]
  x,y=r*math.sin(math.radians(b)),r*math.cos(math.radians(b))
  P=lambda z:tuple(np.int32(E.proj(c,[x,y,z])))
  cv2.line(im,P(0),P(zt),col,1)
  for z in range(0,int(zt)+1,2):
    p=P(z);L=7 if z%10==0 else 3;cv2.line(im,(p[0]-L,p[1]),(p[0]+L,p[1]),col,1)
    if z%10==0:cv2.putText(im,str(z),(p[0]+8,p[1]+4),0,0.35,col,1)
im=im[y0:y1,x0:x1];s=min(2.0,1400/(x1-x0));cv2.imwrite(out,cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC))
