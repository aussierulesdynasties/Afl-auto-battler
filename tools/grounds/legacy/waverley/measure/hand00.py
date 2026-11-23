import cv2,numpy as np,json
H=np.array([(330,97),(510,130),(600,300),(540,470),(330,570),(150,520),(85,330),(130,170)],float)/0.8+[600,560]
cx,cy=H.mean(0);print('centre',cx,cy)
ang=np.degrees(np.arctan2(-(H[:,1]-cy),H[:,0]-cx))%360;rad=np.hypot(H[:,0]-cx,H[:,1]-cy)
def basis(A,K):
    t=np.radians(A);return np.column_stack([np.ones_like(t)]+[f(k*t) for k in range(1,K+1) for f in (np.cos,np.sin)])
c,*_=np.linalg.lstsq(basis(ang,2),rad,rcond=None)
a=cv2.imread('hist_00.png').astype(np.float32);g=cv2.GaussianBlur(a.mean(2),(0,0),1.5)
A=np.arange(0,360,0.5);P=basis(A,2)@c;R=[]
for W in (25,12,6):
    R=[]
    for an,p in zip(A,P):
        t=np.radians(an);rs=np.arange(p-W,p+W,0.25)
        v=np.array([cv2.getRectSubPix(g,(1,1),(cx+r*np.cos(t),cy-r*np.sin(t)))[0,0] for r in rs]);d=np.gradient(v)
        R.append(rs[int(d.argmin())])
    R=np.array(R);keep=np.ones(len(A),bool);K={25:4,12:6,6:10}[W]
    for it in range(6):
        cc,*_=np.linalg.lstsq(basis(A[keep],K),R[keep],rcond=None);res=R-basis(A,K)@cc;s=1.4826*np.median(np.abs(res[keep]));keep=np.abs(res)<max(3*s,1)
    P=basis(A,K)@cc;print(W,K,keep.sum(),'rms px %.2f'%np.sqrt((res[keep]**2).mean()))
json.dump({'cx':cx,'cy':cy,'pts':[[float(x),float(y)] for x,y in zip(A,R)],'c':cc.tolist(),'K':10},open('hand00.json','w'))
im=cv2.imread('hist_00.png')
cv2.polylines(im,[np.stack([cx+P*np.cos(np.radians(A)),cy-P*np.sin(np.radians(A))],1).astype(np.int32)],True,(0,255,255),1)
for x,y in H: cv2.circle(im,(int(x),int(y)),4,(255,0,255),-1)
cv2.imwrite('hand00.jpg',cv2.resize(im[560:1420,600:1480],None,fx=0.8,fy=0.8))
x=P*np.cos(np.radians(A));y=P*np.sin(np.radians(A))
for t in np.radians(np.arange(0,180,15)): print('%3d deg extent %.1f m'%(np.degrees(t),np.ptp(x*np.cos(t)+y*np.sin(t))*0.2791))
