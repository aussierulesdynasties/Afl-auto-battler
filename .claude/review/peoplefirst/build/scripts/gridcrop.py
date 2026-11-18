import cv2,sys,numpy as np
# gridcrop.py img x0 y0 w h scale out
f,x0,y0,w,h,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
a=cv2.imread(f);c=cv2.resize(a[y0:y0+h,x0:x0+w],(w*s,h*s),interpolation=cv2.INTER_CUBIC)
st=10 if w<=200 else 20
for gx in range(((x0+st-1)//st)*st,x0+w,st):
    X=(gx-x0)*s;cv2.line(c,(X,0),(X,8 if gx%(st*5) else 16),(0,255,255),1)
    if gx%(st*5)==0:cv2.putText(c,str(gx),(X+2,28),0,0.45,(0,255,255),1)
for gy in range(((y0+st-1)//st)*st,y0+h,st):
    Y=(gy-y0)*s;cv2.line(c,(0,Y),(8 if gy%(st*5) else 16,Y),(0,255,255),1)
    if gy%(st*5)==0:cv2.putText(c,str(gy),(18,Y+4),0,0.45,(0,255,255),1)
cv2.imwrite(out,c)
