# remove thin diagonal cables (real objects in front of a face) from a rectified texture: python decable.py in out [minlen] [debug]
import sys,cv2,numpy as np,math
im=cv2.imread(sys.argv[1]);g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
minlen=int(sys.argv[3]) if len(sys.argv)>3 else 60
bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
th=cv2.add(bh,0);_,bw=cv2.threshold(th,12,255,cv2.THRESH_BINARY)
L=cv2.HoughLinesP(bw,1,np.pi/360,30,minLineLength=minlen,maxLineGap=12)
mask=np.zeros_like(g);n=0
for l in (L if L is not None else []):
    x1,y1,x2,y2=[int(v) for v in np.ravel(l)[:4]];a=abs(math.degrees(math.atan2(y2-y1,x2-x1)))%180
    if 12<a<78 or 102<a<168:
        cv2.line(mask,(x1,y1),(x2,y2),255,3);n+=1
out=cv2.inpaint(im,mask,3,cv2.INPAINT_TELEA);cv2.imwrite(sys.argv[2],out)
if len(sys.argv)>4:
    dbg=im.copy();dbg[mask>0]=(0,0,255);cv2.imwrite(sys.argv[4],dbg)
print('segments',n)
