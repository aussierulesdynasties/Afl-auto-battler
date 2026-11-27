# fence.py IMG OUT.json : the fence wall itself (thin bright/dark line) within +-W px of the median turf edge (tmed_fit.json)
import cv2,json,numpy as np,sys
d=json.load(open('tmed_fit.json'));c=np.array(d['c']);cx,cy=d['cx'],d['cy'];W=float(sys.argv[3]) if len(sys.argv)>3 else 12
g=cv2.imread(sys.argv[1]).astype(np.float32).mean(2);dog=cv2.GaussianBlur(g,(0,0),1)-cv2.GaussianBlur(g,(0,0),4)
A=np.arange(0,360,0.5);t=np.radians(A)
B=lambda t,K: np.column_stack([np.ones_like(t)]+[q(k*t) for k in range(1,K+1) for q in (np.cos,np.sin)])
P=B(t,10)@c;R=[];S=[]
for a,p in zip(t,P):
    rs=np.arange(p-W,p+3,0.25);v=np.array([cv2.getRectSubPix(dog,(1,1),(cx+r*np.cos(a),cy-r*np.sin(a)))[0,0] for r in rs])
    # fence = a bright-dark pair (top lit, shadow): strongest |dog| ridge; take the mid point of the max and min within 3 px
    e=-v;i=int(e.argmax());R.append(rs[i]);S.append(float(e[i]))
R=np.array(R);S=np.array(S);keep=S>np.percentile(S,20)
for it in range(6):
    cc,*_=np.linalg.lstsq(B(t[keep],10),R[keep],rcond=None);res=R-B(t,10)@cc;sd=1.4826*np.median(np.abs(res[keep]));keep&=np.abs(res)<max(3*sd,1)
print(sys.argv[1],'kept',keep.sum(),'rms px %.2f'%np.sqrt((res[keep]**2).mean()),'mean offset from turf trace px %.2f'%np.mean(B(t,10)@cc-P))
json.dump({'cx':cx,'cy':cy,'K':10,'c':cc.tolist(),'pts':[[float(a),float(r),bool(k)] for a,r,k in zip(A,R,keep)]},open(sys.argv[2],'w'))
