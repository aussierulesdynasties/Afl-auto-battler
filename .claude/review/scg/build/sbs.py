import sys,cv2,numpy as np
x0,y0,x1,y1=map(int,sys.argv[1].split(','));out=sys.argv[2];k=float(sys.argv[3]) if len(sys.argv)>3 else 3
def g(im):
    im=cv2.resize(im[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC)
    for x in range(x0-x0%10+10,x1,10):
        X=int((x-x0)*k);cv2.line(im,(X,0),(X,im.shape[0]),(255,255,0) if x%50==0 else (110,110,30),1)
        if x%50==0:cv2.putText(im,str(x),(X+2,14),0,0.45,(255,255,0),1)
    for y in range(y0-y0%10+10,y1,10):
        Y=int((y-y0)*k);cv2.line(im,(0,Y),(im.shape[1],Y),(255,255,0) if y%50==0 else (110,110,30),1)
        if y%50==0:cv2.putText(im,str(y),(2,Y-2),0,0.45,(255,255,0),1)
    return im
a=cv2.imread('refs/scg.jpg');b=cv2.imread('out/r0.png')
cv2.imwrite(out,np.hstack([g(a.copy()),np.full((int((y1-y0)*k),6,3),255,np.uint8),g(b.copy())]))
