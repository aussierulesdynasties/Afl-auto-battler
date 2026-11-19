# zoom.py x0 y0 x1 y1 out : sat_world crop with the model's top-down edges (1 px red) and a 5 m grid labelled in world X/Y
import numpy as np,cv2,sys
x0,y0,x1,y1=map(int,sys.argv[1:5]);out=sys.argv[5];k=int(sys.argv[6]) if len(sys.argv)>6 else 3
sat=cv2.imread('sat/sat_world.png');t=cv2.imread('sat/top.png',cv2.IMREAD_UNCHANGED);px=0.2;H=170;PC=(0.94,-11.82)
e=cv2.Canny(cv2.cvtColor(t[:,:,:3],cv2.COLOR_BGR2GRAY),30,90)|cv2.Canny(t[:,:,3],50,150)
u=cv2.resize(sat[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_CUBIC);ee=cv2.resize(e[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST)
u[ee>0]=(0,0,255)
for X in range(-200,200,5):
    xp=((X-PC[0]+H)/px-0.5-x0)*k
    if 0<=xp<u.shape[1]:cv2.line(u,(int(xp),0),(int(xp),u.shape[0]),(255,255,0),1);cv2.putText(u,str(X),(int(xp)+2,12),0,0.4,(255,255,0),1)
for Y in range(-200,200,5):
    yp=((PC[1]+H-Y)/px-0.5-y0)*k
    if 0<=yp<u.shape[0]:cv2.line(u,(0,int(yp)),(u.shape[1],int(yp)),(0,255,255),1);cv2.putText(u,str(Y),(2,int(yp)-2),0,0.4,(0,255,255),1)
cv2.imwrite(out,u)
