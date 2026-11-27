# zoom2.py IMG x0 y0 w h s OUT [gain]: zoom with a grid every 5 px (labels every 10) and contrast stretch
import sys,cv2,numpy as np
f,x0,y0,w,h,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7];gain=float(sys.argv[8]) if len(sys.argv)>8 else 1
im=cv2.imread(f)[y0:y0+h,x0:x0+w].astype(np.float32)
lo,hi=np.percentile(im,1),np.percentile(im,99);im=np.clip((im-lo)/(hi-lo)*255*gain,0,255).astype(np.uint8)
im=cv2.resize(im,(w*s,h*s),interpolation=cv2.INTER_CUBIC)
for x in range((x0//5+1)*5,x0+w,5):
    cv2.line(im,((x-x0)*s,0),((x-x0)*s,h*s),(0,255,255) if x%10==0 else (0,110,110),1)
    if x%10==0:cv2.putText(im,str(x),((x-x0)*s+2,10),0,0.33,(0,255,255),1)
for y in range((y0//5+1)*5,y0+h,5):
    cv2.line(im,(0,(y-y0)*s),(w*s,(y-y0)*s),(0,255,255) if y%10==0 else (0,110,110),1)
    if y%10==0:cv2.putText(im,str(y),(2,(y-y0)*s-2),0,0.33,(0,255,255),1)
cv2.imwrite(out,im)
