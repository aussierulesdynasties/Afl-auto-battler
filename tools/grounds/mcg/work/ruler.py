# python work/ruler.py view out "x,y[,label]" ... : draw a 0..80 m height ruler (5 m ticks) at each plan point onto ge/<view>.png
import sys,json,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E
v=sys.argv[1];out=sys.argv[2];C=json.load(open('work/cams.json'))[v];x0,y0,a,d,h,t=C
c=E.cam(h,t,d,tz=a-13,tx=x0,ty=y0);im=cv2.imread(f'ge/{v}.png')
for s in sys.argv[3:]:
  p=s.split(',');x,y=float(p[0]),float(p[1]);lab=p[2] if len(p)>2 else ''
  q0=E.proj(c,(x,y,0));q1=E.proj(c,(x,y,80))
  cv2.line(im,tuple(map(int,q0)),tuple(map(int,q1)),(0,0,255),1)
  for z in range(0,81,5):
    q=E.proj(c,(x,y,z));L=8 if z%10==0 else 4;cv2.line(im,(int(q[0])-L,int(q[1])),(int(q[0])+L,int(q[1])),(0,255,255),1)
    if z%20==0: cv2.putText(im,str(z),(int(q[0])+9,int(q[1])+4),0,0.4,(0,255,255),1)
  cv2.putText(im,lab,(int(q1[0])-10,int(q1[1])-6),0,0.5,(0,0,255),1)
cv2.imwrite(out,im)
