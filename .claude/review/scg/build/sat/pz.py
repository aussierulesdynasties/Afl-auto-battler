# zoomed polar strip of the satellite: pz.py a0 a1 r0 r1 out [traces...]; 10 px/deg, 10 px/m; grid every 5 deg / 5 m
import numpy as np,cv2,sys,json,math
a0,a1,r0,r1=map(float,sys.argv[1:5]);out=sys.argv[5]
im=cv2.imread('sat/sat_world.png');N=1700;H=170.0
A=np.arange(a0,a1,0.1);Rr=np.arange(r0,r1,0.1);aa,rr=np.meshgrid(np.radians(A),Rr)
u=cv2.remap(im,((rr*np.cos(aa)+H)/(2*H)*N-0.5).astype(np.float32),((H-rr*np.sin(aa))/(2*H)*N-0.5).astype(np.float32),cv2.INTER_CUBIC)
T=json.load(open('sat/trace.json'))
for k,c in (('grass',(0,255,0)),('win',(255,0,255)),('wout',(255,0,255))):
    for i,r in enumerate(T[k]):
        d=i/2
        for dd in (d,d-360,d+360):
            if a0<=dd<a1 and r is not None and r0<=r<r1:cv2.circle(u,(int((dd-a0)*10),int((r-r0)*10)),2,c,-1)
for d in range(int(math.ceil(a0/5)*5),int(a1),5):
    x=int((d-a0)*10);cv2.line(u,(x,0),(x,u.shape[0]),(255,255,0),1);cv2.putText(u,str(d),(x+2,14),0,0.45,(255,255,0),1)
for r in range(int(math.ceil(r0/5)*5),int(r1),5):
    y=int((r-r0)*10);cv2.line(u,(0,y),(u.shape[1],y),(0,255,255),1);cv2.putText(u,str(r),(2,y-2),0,0.45,(0,255,255),1)
cv2.imwrite(out,u)
