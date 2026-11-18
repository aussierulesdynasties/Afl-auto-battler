# warp the satellite local plan onto the 2019 aerial (mu.png) as a plane at height z; blend 50%
import sys,os;sys.path.insert(0,os.getcwd())
from frame import *
import cv2
z=float(sys.argv[1]);out=sys.argv[2]
ph=cv2.imread('mu.png');H,W=ph.shape[:2];sat=cv2.imread('../sat/lplan_all_clean.png')
us,vs=np.meshgrid(np.arange(0,W,2),np.arange(0,H,2))
mx=np.zeros(us.shape,np.float32);my=np.zeros(us.shape,np.float32)
for i in range(us.shape[0]):
    for j in range(us.shape[1]):
        try:
            X=at_z(P,us[i,j],vs[i,j],z);s,t=loc(X)[0]
        except Exception:s,t=1e4,1e4
        mx[i,j]=(200-t)/0.25;my[i,j]=(s+200)/0.25
mx=cv2.resize(mx,(W,H));my=cv2.resize(my,(W,H))
w=cv2.remap(sat,mx,my,cv2.INTER_LINEAR,borderValue=(0,0,0))
cv2.imwrite(out,cv2.addWeighted(ph,0.5,w,0.5,0))
