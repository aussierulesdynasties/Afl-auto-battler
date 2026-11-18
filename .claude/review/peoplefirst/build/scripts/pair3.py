import sys,cv2,numpy as np
x0,y0,x1,y1=map(int,sys.argv[2:6]);k=float(sys.argv[6])
P=cv2.imread('photo.png');S=cv2.imread('sat.png');Hc=np.load('Hc.npy')
Wp=cv2.warpPerspective(S,Hc,(2000,1333))
def g(im):
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=k,fy=k)
    for x in range((x0//10+1)*10,x1,10):
        X=int((x-x0)*k);cv2.line(c,(X,0),(X,c.shape[0]),(0,0,255) if x%50==0 else (90,90,90),1)
        if x%50==0:cv2.putText(c,str(x),(X+2,12),0,0.4,(0,255,255),1)
    for y in range((y0//10+1)*10,y1,10):
        Y=int((y-y0)*k);cv2.line(c,(0,Y),(c.shape[1],Y),(0,0,255) if y%50==0 else (90,90,90),1)
        if y%50==0:cv2.putText(c,str(y),(2,Y-2),0,0.4,(0,255,255),1)
    return c
cv2.imwrite(sys.argv[1],np.vstack([g(P),g(Wp)]))
