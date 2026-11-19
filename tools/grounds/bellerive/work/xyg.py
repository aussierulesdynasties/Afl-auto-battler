# python work/xyg.py img out x0 x1 y0 y1 [scale] : crop of a 0.25 m/px Esri-frame ortho with an x/y metre grid every 5 m (labels every 10)
import sys,cv2
im=cv2.imread(sys.argv[1]);out=sys.argv[2];x0,x1,y0,y1=map(float,sys.argv[3:7]);s=float(sys.argv[7]) if len(sys.argv)>7 else 2
P=lambda x,y:(int((x+200)*4),int((200-y)*4))
a,b=P(x0,y1);c,d=P(x1,y0);cr=cv2.resize(im[b:d,a:c],None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
for g in range(int(x0)//5*5,int(x1)+1,5):
  u=int(((g+200)*4-a)*s);cv2.line(cr,(u,0),(u,cr.shape[0]),(0,255,255) if g%10==0 else (0,160,160),1)
  if g%10==0:cv2.putText(cr,str(g),(u+2,14),0,0.45,(0,255,255),1)
for g in range(int(y0)//5*5,int(y1)+1,5):
  v=int(((200-g)*4-b)*s);cv2.line(cr,(0,v),(cr.shape[1],v),(255,0,255) if g%10==0 else (160,0,160),1)
  if g%10==0:cv2.putText(cr,str(g),(2,v-2),0,0.45,(255,0,255),1)
cv2.imwrite(out,cr)
