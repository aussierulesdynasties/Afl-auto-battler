import json,numpy as np,cv2,sys
j=json.load(open('fit.json'));s=j['scale_m_px'];cx,cy=j['cx'],j['cy'];K=j['K'];c=np.array(j['c'])
def B(a,K):
    t=np.radians(a);return np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
for f in sys.argv[1:]:
    g=cv2.GaussianBlur(cv2.imread(f,0).astype(np.float32),(0,0),1)
    A=np.arange(0,360,1.0);R=B(A,K)@c;out=[]
    for a,r in zip(A,R):
        t=np.radians(a);rs=np.arange(r,r+25,0.25)
        v=np.array([cv2.getRectSubPix(g,(1,1),(cx+q*np.cos(t),cy-q*np.sin(t)))[0,0] for q in rs])
        k=int(v.argmax());out.append((a,rs[k]-r,v[k]))
    out=np.array(out)
    for a0 in range(0,360,30):
        m=(out[:,0]>=a0)&(out[:,0]<a0+30);print(f,a0,'peak at +%.1f m (bright %.0f)'%(np.median(out[m,1])*s,np.median(out[m,2])))
