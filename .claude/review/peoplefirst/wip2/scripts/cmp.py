# side-by-side photo | render crop with pixel-labelled grid. usage: python cmp.py render.png x0 y0 x1 y1 scale out.png [step]
import cv2,numpy as np,sys
rp,x0,y0,x1,y1,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7];st=int(sys.argv[8]) if len(sys.argv)>8 else 10
ph=cv2.imread('photo_clean.png');r=cv2.imread(rp,cv2.IMREAD_UNCHANGED);a=r[:,:,3:4]/255.0
ren=(r[:,:,:3]*a+np.array([150,220,120])*(1-a)).astype(np.uint8)
def g(im):
    c=cv2.resize(im[y0:y1,x0:x1],None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
    for x in range((x0//st+1)*st,x1,st):
        X=(x-x0)*s;cv2.line(c,(X,0),(X,c.shape[0]),(0,255,255) if x%(st*5)==0 else (0,160,160),1)
        if x%(st*5)==0:cv2.putText(c,str(x),(X+2,12),0,0.4,(0,255,255),1)
    for y in range((y0//st+1)*st,y1,st):
        Y=(y-y0)*s;cv2.line(c,(0,Y),(c.shape[1],Y),(255,0,255) if y%(st*5)==0 else (160,0,160),1)
        if y%(st*5)==0:cv2.putText(c,str(y),(2,Y-2),0,0.4,(255,0,255),1)
    return c
cv2.imwrite(out,np.hstack([g(ph),np.full(((y1-y0)*s,6,3),255,np.uint8),g(ren)]))
