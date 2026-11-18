import cv2,numpy as np,sys
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);p=cv2.imread('photo.png')
a=r[:,:,3];rgb=r[:,:,:3]
e=cv2.Canny(cv2.cvtColor(rgb,cv2.COLOR_BGR2GRAY),40,120)|cv2.Canny(a,50,150)
e=cv2.dilate(e,np.ones((2,2),np.uint8))
o=p.copy();o[e>0]=(255,255,0)
cv2.imwrite(sys.argv[2]+'_lines.jpg',cv2.resize(o,(1400,933),interpolation=cv2.INTER_AREA))
if len(sys.argv)>3:
    x0,y0,x1,y1=map(int,sys.argv[3:7]);cv2.imwrite(sys.argv[2]+'_zl.jpg',o[y0:y1,x0:x1])
