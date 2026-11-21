import sys,cv2
v,out=sys.argv[1],sys.argv[2];x0,y0,x1,y1=map(int,sys.argv[3:7]);k=float(sys.argv[7]);p=cv2.imread(f'ge/{v}.png')
c=cv2.resize(p[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC)
for x in range((x0//10+1)*10,x1,10):
    X=int((x-x0)*k);L=14 if x%50==0 else 6;cv2.line(c,(X,0),(X,L),(0,255,255),1)
    if x%50==0:cv2.putText(c,str(x),(X+2,26),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
for y in range((y0//10+1)*10,y1,10):
    Y=int((y-y0)*k);L=14 if y%50==0 else 6;cv2.line(c,(0,Y),(L,Y),(0,255,255),1)
    if y%50==0:cv2.putText(c,str(y),(16,Y+4),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
cv2.imwrite(out,c)
