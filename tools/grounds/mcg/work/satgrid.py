# python work/satgrid.py x0 y0 x1 y1 out [scale]: local-metre crop of sat/esri_025.png with a labelled 10 m grid
import sys,cv2
x0,y0,x1,y1=map(float,sys.argv[1:5]);out=sys.argv[5];sc=float(sys.argv[6]) if len(sys.argv)>6 else 1
I=cv2.imread('sat/esri_025.png');H=260;R=0.25
c=lambda x,y:(int((x+H)/R),int((H-y)/R))
a,b=c(x0,y1);e,f=c(x1,y0);im=I[b:f,a:e].copy()
im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
P=lambda x,y:(int(((x+H)/R-a)*sc),int(((H-y)/R-b)*sc))
for g in range(-260,261,10):
  col=(0,255,255) if g%50==0 else (200,200,200)
  if x0<=g<=x1:
    p=P(g,0)[0];cv2.line(im,(p,0),(p,im.shape[0]),col,1);cv2.putText(im,str(g),(p+2,12),0,0.4,col,1)
  if y0<=g<=y1:
    q=P(0,g)[1];cv2.line(im,(0,q),(im.shape[1],q),col,1);cv2.putText(im,str(g),(2,q-2),0,0.4,col,1)
cv2.imwrite(out,im)
