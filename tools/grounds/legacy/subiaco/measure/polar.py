# polar.py IMG cx cy mpp OUT [rmin rmax] : unwrap round (cx,cy): x = bearing (deg, 0 = east, counter-clockwise = north is 90), 4 px/deg; y = radius m, 4 px/m, outward down
import sys,cv2,numpy as np
f,cx,cy,mpp,out=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
r0,r1=(float(sys.argv[6]),float(sys.argv[7])) if len(sys.argv)>7 else (55,175)
im=cv2.imread(f);A=np.radians(np.arange(0,360,0.25));R=np.arange(r0,r1,0.25)
X=(cx+np.outer(R,np.cos(A))/mpp).astype(np.float32);Y=(cy-np.outer(R,np.sin(A))/mpp).astype(np.float32)
P=cv2.remap(im,X,Y,cv2.INTER_CUBIC)
for b in range(0,360,10):
    cv2.line(P,(b*4,0),(b*4,8 if b%30 else 20),(0,255,255),1);cv2.putText(P,str(b),(b*4+2,30),0,0.35,(0,255,255),1) if b%30==0 else None
for r in range(int(r0)//10*10+10,int(r1),10):
    y=int((r-r0)*4);cv2.line(P,(0,y),(12,y),(0,255,255),1);cv2.putText(P,str(r),(14,y+4),0,0.35,(0,255,255),1)
cv2.imwrite(out,P)
