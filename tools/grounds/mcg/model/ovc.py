import sys,cv2,numpy as np
# python model/ovc.py view out x0 y0 x1 y1 [scale] : photo with render edges (red) + render silhouette (cyan), cropped, gridded
v,out=sys.argv[1],sys.argv[2];x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7]) if len(sys.argv)>7 else 2
p=cv2.imread(f'ge/{v}.png');import os;r=cv2.imread(f"{os.environ.get('RR','rr')}/{v}.png",cv2.IMREAD_UNCHANGED)
q=r[:,:,:3].astype(int);e=((np.abs(np.diff(q,axis=0,prepend=q[:1])).sum(2)>30)|(np.abs(np.diff(q,axis=1,prepend=q[:,:1])).sum(2)>30)).astype(np.uint8)
s=cv2.Canny(r[:,:,3],50,150)
o=p.copy();o[e>0]=(0,0,255);o[s>0]=(255,255,0)
c=o[y0:y1,x0:x1];c=cv2.resize(c,None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
for x in range((x0//20+1)*20,x1,20):
    X=int((x-x0)*k);cv2.line(c,(X,0),(X,8),(0,255,255),1)
    if x%100==0:cv2.putText(c,str(x),(X+2,20),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
for y in range((y0//20+1)*20,y1,20):
    Y=int((y-y0)*k);cv2.line(c,(0,Y),(8,Y),(0,255,255),1)
    if y%100==0:cv2.putText(c,str(y),(10,Y+4),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
cv2.imwrite(out,c)
