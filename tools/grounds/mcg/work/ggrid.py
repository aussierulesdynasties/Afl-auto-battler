# python work/ggrid.py view u0 v0 u1 v1 out [scale] : crop a GE view with pixel labels every 20 px (labels every 100)
import sys,cv2
v=sys.argv[1];u0,v0,u1,v1=map(int,sys.argv[2:6]);out=sys.argv[6];s=float(sys.argv[7]) if len(sys.argv)>7 else 2
im=cv2.imread(v if v.endswith('.png') else f'ge/{v}.png')[v0:v1,u0:u1];im=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
for u in range((u0//20+1)*20,u1,20):
    x=int((u-u0)*s);c=(0,255,255) if u%100==0 else (0,160,160);cv2.line(im,(x,0),(x,im.shape[0]),c,1)
    if u%100==0 or s>=3: cv2.putText(im,str(u),(x+2,12),0,0.4,(0,255,255),1)
for w in range((v0//20+1)*20,v1,20):
    y=int((w-v0)*s);c=(0,255,255) if w%100==0 else (0,160,160);cv2.line(im,(0,y),(im.shape[1],y),c,1)
    if w%100==0 or s>=3: cv2.putText(im,str(w),(2,y-2),0,0.4,(0,255,255),1)
cv2.imwrite(out,im)
