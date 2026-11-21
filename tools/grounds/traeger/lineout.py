# Refine each rough straight cable line to the darkest thin line nearby, then inpaint it.
# python lineout.py in out "x1,y1,x2,y2 ..." [width] [debug]
import sys,cv2,numpy as np
im=cv2.imread(sys.argv[1]);g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
w=int(sys.argv[4]) if len(sys.argv)>4 else 3;H,W=g.shape;m=np.zeros((H,W),np.uint8)
def score(x1,y1,x2,y2):
    n=int(np.hypot(x2-x1,y2-y1));t=np.linspace(0,1,n);xs=x1+(x2-x1)*t;ys=y1+(y2-y1)*t
    ok=(xs>=0)&(xs<W-1)&(ys>=0)&(ys<H-1);return bh[ys[ok].astype(int),xs[ok].astype(int)].mean() if ok.sum()>10 else 0
for s in sys.argv[3].split():
    x1,y1,x2,y2=map(float,s.split(','));best=(score(x1,y1,x2,y2),0,0)
    for d1 in np.arange(-6,6.5,0.5):
        for d2 in np.arange(-6,6.5,0.5):
            sc=score(x1+d1,y1,x2+d2,y2)
            if sc>best[0]:best=(sc,d1,d2)
    sc,d1,d2=best;print(s,'->',x1+d1,x2+d2,round(sc,1))
    cv2.line(m,(round(x1+d1),round(y1)),(round(x2+d2),round(y2)),255,w)
cv2.imwrite(sys.argv[2],cv2.inpaint(im,m,5,cv2.INPAINT_NS))
if len(sys.argv)>5:
    d=im.copy();d[m>0]=(0,0,255);cv2.imwrite(sys.argv[5],d)
