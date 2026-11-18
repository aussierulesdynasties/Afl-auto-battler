# rectify a quad (tl,tr,br,bl) of a photo to a W x H texture: python rect.py src out W H x1 y1 x2 y2 x3 y3 x4 y4
import cv2,numpy as np,sys
a=sys.argv;im=cv2.imread(a[1]);W,H=int(a[3]),int(a[4]);q=np.array(list(map(float,a[5:13]))).reshape(4,2).astype(np.float32)
M=cv2.getPerspectiveTransform(q,np.float32([[0,0],[W,0],[W,H],[0,H]]))
cv2.imwrite(a[2],cv2.warpPerspective(im,M,(W,H),flags=cv2.INTER_LANCZOS4))
