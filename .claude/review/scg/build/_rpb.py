# M-frame rotated plan of the aerial photo at height z with every BLD block drawn (eave outline). python _rpb.py z out
import numpy as np,cv2,math,sys
exec(open('meas.py').read());exec(open('blds.py').read())
img=cv2.imread('refs/scg.jpg');z=float(sys.argv[1]);S=10;FRM=sys.argv[3] if len(sys.argv)>3 else 'M'
(ox,oy),ang=FR[FRM];u0,u1,w0,w1=(-50,62,-5,62) if FRM=='M' else (-10,75,-10,55)
a=math.radians(ang);U=np.array([math.cos(a),math.sin(a)]);Wd=np.array([-U[1],U[0]]);O=np.array([ox,oy])
W=int((u1-u0)*S);H=int((w1-w0)*S)
us=u0+(np.arange(W)+0.5)/S;ws=w1-(np.arange(H)+0.5)/S
gu,gw=np.meshgrid(us,ws);XY=O+gu[...,None]*U+gw[...,None]*Wd
uv=pr(np.c_[XY.reshape(-1,2),np.full(gu.size,z)]).reshape(H,W,2).astype(np.float32)
out=cv2.remap(img,uv[...,0],uv[...,1],cv2.INTER_CUBIC);out=out[:,::-1].copy()   # mirror so the plan reads like the photo (u grows to the left)
def px(p):d=p-O;return (int(W-1-(d@U-u0)*S),int((w1-d@Wd)*S))
for m in range(int(u0),int(u1)+1,5):
    x=int(W-1-(m-u0)*S);cv2.line(out,(x,0),(x,H),(0,0,255) if m%10==0 else (120,120,230),1);cv2.putText(out,str(m),(x+2,12),0,0.4,(0,255,255),1)
for m in range(int(w0),int(w1)+1,5):
    y=int((w1-m)*S);cv2.line(out,(0,y),(W,y),(0,0,255) if m%10==0 else (120,120,230),1);cv2.putText(out,str(m),(2,y-2),0,0.4,(0,255,255),1)
for b in BLD:
    n,f,a0,a1,b0,b1=b[:6];(fx,fy),fa=FR[f];fa=math.radians(fa);FU=np.array([math.cos(fa),math.sin(fa)]);FW=np.array([-FU[1],FU[0]]);FO=np.array([fx,fy])
    c=[FO+uu*FU+ww*FW for uu,ww in ((a0,b0),(a1,b0),(a1,b1),(a0,b1))]
    cv2.polylines(out,[np.array([px(p) for p in c])],True,(255,255,255),2);m_=sum(c)/4;cv2.putText(out,n,px(m_),0,0.6,(255,255,255),2)
cv2.imwrite(sys.argv[2],out)
