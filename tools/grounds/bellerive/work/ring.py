# python work/ring.py view out "b0,b1,r0,r1,z0,z1[,colour]" ... : polar polylines (r and z linear from b0 to b1) projected into a GE view; ticks every 10 deg
import sys,math,cv2,numpy as np;sys.path.insert(0,'work');import tri as T,earthcam as E
v,out=sys.argv[1],sys.argv[2];im=cv2.imread(f'ge/{v}.png');c=T.camv(v)
C=[(255,0,255),(0,255,255),(0,128,255),(0,255,0),(255,255,0),(0,0,255)]
for k,a in enumerate(sys.argv[3:]):
  f=[float(x) for x in a.split(',')];b0,b1,r0,r1,z0,z1=f[:6];col=C[int(f[6]) if len(f)>6 else k%6]
  bs=np.linspace(b0,b1,max(2,int(abs(b1-b0)*2)+1));t=(bs-b0)/(b1-b0 if b1!=b0 else 1)
  P=[E.proj(c,[(r0+(r1-r0)*s)*math.sin(math.radians(b)),(r0+(r1-r0)*s)*math.cos(math.radians(b)),z0+(z1-z0)*s]) for b,s in zip(bs,t)]
  cv2.polylines(im,[np.array(P,np.int32)],False,col,1)
  for b,p in zip(bs,P):
    if abs(b%10)<1e-6:cv2.circle(im,tuple(np.int32(p)),3,col,-1)
cv2.imwrite(out,im)
