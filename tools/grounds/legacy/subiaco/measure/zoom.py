# zoom.py IMG x0 y0 w h scale OUT : crop with a labelled pixel grid every 10 px (labels every 50) in full-image coords
import sys,cv2
f,x0,y0,w,h,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
im=cv2.imread(f)[y0:y0+h,x0:x0+w];im=cv2.resize(im,(w*s,h*s),interpolation=cv2.INTER_CUBIC)
for x in range((x0//10+1)*10,x0+w,10):
    c=(0,255,255) if x%50==0 else (0,120,120);cv2.line(im,((x-x0)*s,0),((x-x0)*s,h*s),c,1)
    if x%50==0:cv2.putText(im,str(x),((x-x0)*s+2,12),0,0.4,(0,255,255),1)
for y in range((y0//10+1)*10,y0+h,10):
    c=(0,255,255) if y%50==0 else (0,120,120);cv2.line(im,(0,(y-y0)*s),(w*s,(y-y0)*s),c,1)
    if y%50==0:cv2.putText(im,str(y),(2,(y-y0)*s-2),0,0.4,(0,255,255),1)
cv2.imwrite(out,im)
