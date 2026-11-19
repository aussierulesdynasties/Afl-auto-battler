# polar unwrap of a world-grid image (0.2 m/px, 340 m square centred on PC): x = angle 0..360 (2 px/deg), y = r 50..175 m (4 px/m, r grows down)
import numpy as np,cv2,sys,math
im=cv2.imread(sys.argv[1]);N=im.shape[0];H=170.0
A=np.arange(0,360,0.5);Rr=np.arange(50,175,0.25)
aa,rr=np.meshgrid(np.radians(A),Rr)
X=rr*np.cos(aa);Y=rr*np.sin(aa)   # relative to PC
mx=((X+H)/(2*H)*N-0.5).astype(np.float32);my=((H-Y)/(2*H)*N-0.5).astype(np.float32)
u=cv2.remap(im,mx,my,cv2.INTER_LINEAR)
for d in range(0,360,10):
    cv2.line(u,(d*2,0),(d*2,u.shape[0]),(255,255,0) if d%30==0 else (120,120,0),1)
    if d%30==0:cv2.putText(u,str(d),(d*2+2,12),0,0.4,(255,255,0),1)
for r in range(60,175,10):
    y=int((r-50)*4);cv2.line(u,(0,y),(720,y),(0,255,255),1);cv2.putText(u,str(r),(2,y-2),0,0.35,(0,255,255),1)
cv2.imwrite(sys.argv[2],u)
