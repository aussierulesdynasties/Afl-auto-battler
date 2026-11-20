# python model/ruler.py view out zmax x,y [x,y ...] : photo crop with a vertical metre ruler (ticks every 0.5 m) at each ground point
import sys,cv2,numpy as np,re
sys.path.insert(0,'work');import earthcam as E
G={'nw':(-62,58),'n':(-15,80),'ne':(62,60),'e':(79,-8),'e2':(76,-46),'se':(60,-90),'s':(51,-120),'w':(-80,-20)}
v=sys.argv[1];out=sys.argv[2];zm=float(sys.argv[3]);pts=[tuple(map(float,a.split(','))) for a in sys.argv[4:]]
g,h=re.match(r'g_(\w+)_(\d+)',v).groups();c=E.cam(int(h),60,140,tz=1,tx=G[g][0],ty=G[g][1])
im=cv2.imread(f'ge/{v}.png');Q=[]
for x,y in pts:
  for k in range(int(zm*2)+1):
    z=k/2;p=E.proj(c,(x,y,z));Q.append(p)
    q=E.proj(c,(x,y,z+0.5)) if k<zm*2 else p
    col=(0,255,255) if k%2==0 else (0,140,255)
    cv2.line(im,tuple(p.astype(int)),tuple(q.astype(int)),(255,0,255),1)
    cv2.line(im,tuple((p+[-6 if k%2==0 else -3,0]).astype(int)),tuple((p+[6 if k%2==0 else 3,0]).astype(int)),col,1)
    if k%4==0:cv2.putText(im,str(int(z)),tuple((p+[8,4]).astype(int)),0,0.35,(0,255,255),1)
Q=np.array(Q);u0,v0=Q.min(0)-60;u1,v1=Q.max(0)+60
cr=im[max(int(v0),0):int(v1),max(int(u0),0):int(u1)];s=900/cr.shape[0]
cv2.imwrite(out,cv2.resize(cr,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC))
