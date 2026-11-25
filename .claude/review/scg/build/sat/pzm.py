# pz.py with the model's top-down edges (red) on the satellite: pzm.py a0 a1 r0 r1 out
import numpy as np,cv2,sys,math
a0,a1,r0,r1=map(float,sys.argv[1:5]);out=sys.argv[5]
N=1700;H=170.0;A=np.arange(a0,a1,0.1);Rr=np.arange(r0,r1,0.1);aa,rr=np.meshgrid(np.radians(A),Rr)
mx=((rr*np.cos(aa)+H)/(2*H)*N-0.5).astype(np.float32);my=((H-rr*np.sin(aa))/(2*H)*N-0.5).astype(np.float32)
u=cv2.remap(cv2.imread('sat/sat_world.png'),mx,my,cv2.INTER_CUBIC)
t=cv2.imread('sat/top.png',cv2.IMREAD_UNCHANGED);tm=cv2.remap(t,mx,my,cv2.INTER_NEAREST)
g=cv2.cvtColor(tm[:,:,:3],cv2.COLOR_BGR2GRAY);e=cv2.Canny(g,30,90)
if tm.shape[2]==4:e|=cv2.Canny(tm[:,:,3],50,150)
u[cv2.dilate(e,np.ones((2,2),np.uint8))>0]=(0,0,255)
for d in range(int(math.ceil(a0/5)*5),int(a1),5):
    x=int((d-a0)*10);cv2.line(u,(x,0),(x,u.shape[0]),(255,255,0),1);cv2.putText(u,str(d),(x+2,14),0,0.45,(255,255,0),1)
for r in range(int(math.ceil(r0/5)*5),int(r1),5):
    y=int((r-r0)*10);cv2.line(u,(0,y),(u.shape[1],y),(0,255,255),1);cv2.putText(u,str(r),(2,y-2),0,0.45,(0,255,255),1)
cv2.imwrite(out,u)
