import cv2,numpy as np,sys
src,out,npy,cx,cy=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
im=cv2.imread(src);b=cv2.medianBlur(im,9)
hsv=cv2.cvtColor(b,cv2.COLOR_BGR2HSV).astype(int)
ref=np.median(hsv[cy-20:cy+20,cx-20:cx+20].reshape(-1,3),0)
m=((abs(hsv[...,0]-ref[0])<9)&(hsv[...,1]>ref[1]*0.55)&(hsv[...,2]>ref[2]*0.5)).astype(np.uint8)
n,l=cv2.connectedComponents(m);g=(l==l[cy,cx]).astype(np.uint8)
g=cv2.morphologyEx(g,cv2.MORPH_CLOSE,np.ones((21,21),np.uint8))
cs,_=cv2.findContours(g,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);C=max(cs,key=cv2.contourArea)[:,0]
o=im.copy();cv2.drawContours(o,[C],-1,(0,0,255),2);cv2.imwrite(out,o)
np.save(npy,C[::max(1,len(C)//300)].astype(float));print(ref,len(C),g.sum())
