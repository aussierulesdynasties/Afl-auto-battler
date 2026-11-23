# trace.py IMG OUT.json x0 y0 f "x,y;x,y;..." : turf edge from a hand prior (points in a crop at offset x0,y0 scaled f), greenness G-R steepest drop
import cv2,numpy as np,json,sys
img,out=sys.argv[1:3];x0,y0,f=map(float,sys.argv[3:6])
H=np.array([[float(v) for v in p.split(',')] for p in sys.argv[6].split(';')])/f+[x0,y0]
cx,cy=H.mean(0)
a=cv2.imread(img).astype(np.float32);g=cv2.GaussianBlur(a[:,:,1]-a[:,:,2],(0,0),1.5)
def basis(A,K):
    t=np.radians(A);return np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
ang=np.degrees(np.arctan2(-(H[:,1]-cy),H[:,0]-cx))%360;rad=np.hypot(H[:,0]-cx,H[:,1]-cy)
c,*_=np.linalg.lstsq(basis(ang,2),rad,rcond=None);A=np.arange(0,360,0.5);P=basis(A,2)@c
for W,K in ((25,4),(12,6),(6,10)):
    R=[]
    for an,p in zip(A,P):
        t=np.radians(an);rs=np.arange(p-W,p+W,0.25)
        v=np.array([cv2.getRectSubPix(g,(1,1),(cx+r*np.cos(t),cy-r*np.sin(t)))[0,0] for r in rs]);R.append(rs[int(np.gradient(v).argmin())])
    R=np.array(R);keep=np.ones(len(A),bool)
    for it in range(6):
        cc,*_=np.linalg.lstsq(basis(A[keep],K),R[keep],rcond=None);res=R-basis(A,K)@cc;s=1.4826*np.median(np.abs(res[keep]));keep=np.abs(res)<max(3*s,1)
    P=basis(A,K)@cc;print(W,K,keep.sum(),'rms px %.2f'%np.sqrt((res[keep]**2).mean()))
json.dump({'cx':cx,'cy':cy,'K':10,'c':cc.tolist(),'pts':[[float(x),float(y),bool(k)] for x,y,k in zip(A,R,keep)]},open(out,'w'))
im=cv2.imread(img);cv2.polylines(im,[np.stack([cx+P*np.cos(np.radians(A)),cy-P*np.sin(np.radians(A))],1).astype(np.int32)],True,(0,255,255),1)
cv2.imwrite(out.replace('.json','.jpg'),im[int(cy-450):int(cy+450),int(cx-380):int(cx+380)])
