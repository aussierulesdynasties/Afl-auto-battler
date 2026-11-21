# python work/zruler.py out view:b:r[:z0:z1] ... : photo | render crops with a z ruler (1 m ticks) standing at bearing b, radius r
import sys,cv2,numpy as np,math;sys.path.insert(0,'work');import tri,earthcam as E
out=sys.argv[1];tiles=[]
for a in sys.argv[2:]:
    p=a.split(':');v=p[0];b=float(p[1]);r=float(p[2]);z0=float(p[3]) if len(p)>3 else 10;z1=float(p[4]) if len(p)>4 else 46
    c=tri.camv(v);x,y=r*math.sin(math.radians(b)),r*math.cos(math.radians(b))
    pts=[E.proj(c,np.array([x,y,z])) for z in np.arange(z0,z1+0.01,1)]
    ph=cv2.imread(f'ge/{v}.png');rr=cv2.imread(f'rr/{v}.png',cv2.IMREAD_UNCHANGED);al=rr[:,:,3:4]/255.;rn=(rr[:,:,:3]*al+np.array([60,60,60])*(1-al)).astype(np.uint8)
    u=int(np.mean([q[0] for q in pts]));w0=int(min(q[1] for q in pts))-15;w1=int(max(q[1] for q in pts))+15
    h=w1-w0;k=max(1.0,360/h);hw=int(110/k*1.0)+40
    row=[]
    for im in (ph,rn):
        im=im.copy()
        for i,q in enumerate(pts):
            zz=z0+i;L=8 if zz%5 else 16
            cv2.line(im,(int(q[0])-L,int(q[1])),(int(q[0]),int(q[1])),(0,255,255) if zz%5 else (0,0,255),1)
        cr=im[max(w0,0):w1,max(u-hw,0):u+hw];cr=cv2.resize(cr,None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC)
        for i,q in enumerate(pts):
            zz=z0+i
            if zz%5==0:cv2.putText(cr,str(int(zz)),(int((q[0]-max(u-hw,0))*k)-50,int((q[1]-max(w0,0))*k)+5),0,0.5,(0,0,255),2)
        row.append(cr)
    t=np.hstack(row);cv2.putText(t,f'{v} b{b:g} r{r:g}',(5,18),0,0.6,(255,255,0),2);tiles.append(t)
W=max(t.shape[1] for t in tiles);tiles=[cv2.copyMakeBorder(t,0,4,0,W-t.shape[1],cv2.BORDER_CONSTANT) for t in tiles]
cv2.imwrite(out,np.vstack(tiles))
