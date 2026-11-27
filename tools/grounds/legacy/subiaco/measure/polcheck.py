# polcheck.py IMG TRACE.json OUTPREFIX [r0 r1] [col]: polar strip (8 px/deg, 8 px/m) with the trace in red, in 4 quarter images
import sys,cv2,numpy as np,json
f,tj,op=sys.argv[1:4];r0,r1=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (48,105);col=int(sys.argv[6]) if len(sys.argv)>6 else 1
cx,cy,mpp=941,1021,0.2945
im=cv2.imread(f);A=np.radians(np.arange(0,360,0.125));R=np.arange(r0,r1,0.125)
X=(cx+np.outer(R,np.cos(A))/mpp).astype(np.float32);Y=(cy-np.outer(R,np.sin(A))/mpp).astype(np.float32)
P=cv2.remap(im,X,Y,cv2.INTER_CUBIC)
for a,*v in json.load(open(tj)):
    rv=v[col-1]
    if rv and r0<rv<r1:cv2.circle(P,(int(a*8),int((rv-r0)*8)),1,(0,0,255),-1)
for b in range(0,360,5):
    cv2.line(P,(b*8,0),(b*8,6 if b%15 else 16),(0,255,255),1)
    if b%15==0:cv2.putText(P,str(b),(b*8+2,26),0,0.4,(0,255,255),1)
for r in range(int(r0)//5*5+5,int(r1),5):
    y=int((r-r0)*8);cv2.line(P,(0,y),(10,y),(0,255,255),1);cv2.putText(P,str(r),(12,y+4),0,0.35,(0,255,255),1)
for i in range(4):cv2.imwrite(f'{op}_{i}.jpg',P[:,i*720:(i+1)*720])
