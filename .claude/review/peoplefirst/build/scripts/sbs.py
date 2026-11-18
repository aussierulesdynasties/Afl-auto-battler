import cv2,numpy as np,sys
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);p=cv2.imread('photo.png')
a=r[:,:,3:4]/255.0;c=(r[:,:,:3]*a+p*(1-a)).astype(np.uint8)
x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7]) if len(sys.argv)>7 else 1.0
im=np.hstack([p[y0:y1,x0:x1],c[y0:y1,x0:x1]]) if (x1-x0)<(y1-y0)*1.3 else np.vstack([p[y0:y1,x0:x1],c[y0:y1,x0:x1]])
cv2.imwrite(sys.argv[2],cv2.resize(im,None,fx=k,fy=k,interpolation=cv2.INTER_AREA))
