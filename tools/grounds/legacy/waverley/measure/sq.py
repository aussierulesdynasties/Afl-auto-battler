import cv2,numpy as np,sys
g=cv2.imread(sys.argv[1]).astype(np.float32).mean(2)
bg=cv2.medianBlur(g.astype(np.uint8),15).astype(np.float32);t=np.clip(g-bg,0,60)
C=np.array([[1054.0, 900.4], [1147.8, 1055.3], [994.6, 1147.5], [902.5, 995.0]])+[float(sys.argv[2]),float(sys.argv[3])]
lines=[]
for i in range(4):
    p,q=C[i],C[(i+1)%4];d=(q-p)/np.linalg.norm(q-p);n=np.array([-d[1],d[0]]);pts=[]
    for s in np.linspace(0.12,0.88,60):
        c=p+(q-p)*s;off=np.arange(-6,6.01,0.25);v=np.array([cv2.getRectSubPix(t,(1,1),tuple(c+n*o))[0,0] for o in off])
        if v.max()<5: continue
        w=np.clip(v-v.max()*0.5,0,None);pts.append(c+n*(w@off/w.sum()))
    pts=np.array(pts)
    for it in range(3):
        m=pts.mean(0);u,s_,vt=np.linalg.svd(pts-m);r=(pts-m)@vt[1];pts=pts[np.abs(r)<max(2.5*np.std(r),0.5)]
    lines.append((m,vt[0]));print(i,len(pts),'rms %.2f'%np.std(r))
def X(a,b):
    (p,d),(q,e)=a,b;A=np.array([d,-e]).T;t=np.linalg.solve(A,q-p);return p+d*t[0]
K=[X(lines[i-1],lines[i]) for i in range(4)]
L=[np.linalg.norm(K[i]-K[(i+1)%4]) for i in range(4)];print(np.round(L,2),'m/px %.4f'%(50/np.mean(L)),'centre',np.round(np.mean(K,0),1))
