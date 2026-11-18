import cv2,numpy as np,json,sys
from meas import *
S=json.load(open('sat.json'));m=S['mpp']
# homography sat px -> photo via camera on z=0
sp=np.float32([[0,0],[2304,0],[2304,2304],[0,2304],[1152,1152]])
wp=np.array([((x-S['px'])*m,-(y-S['py'])*m,0) for x,y in sp]);pp=pr(wp).astype(np.float32)
Hc,_=cv2.findHomography(sp,pp);np.save('Hc.npy',Hc)
ph=cv2.imread('photo.png');warp=cv2.warpPerspective(cv2.imread('sat.png'),Hc,(2000,1333))
ov=cv2.addWeighted(ph,0.5,warp,0.5,0);cv2.imwrite(sys.argv[1] if len(sys.argv)>1 else 'cam_ov.jpg',cv2.resize(ov,(1400,933)))
