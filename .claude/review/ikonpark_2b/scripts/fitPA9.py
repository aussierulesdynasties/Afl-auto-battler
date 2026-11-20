import json,numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
exec(open('w/fitPA4.py').read().split(chr(10)+'best=None')[0])
L=np.array(g['390148642']);OUT=L[1:22]
OD=np.concatenate([np.linspace(OUT[i],OUT[i+1],20,endpoint=False) for i in range(len(OUT)-1)])
FB=[(205,489),(213,500),(225,520),(245,544),(265,562),(283,572)]
def res6(q):
    p=q[:9];M=R(*p[3:6]);off=q[9]
    X=np.c_[D2+Nn*off,np.zeros(len(D2))];P2=proj(p,X)
    r=list(cKDTree(P2).query(E)[0])+list(cKDTree(E).query(P2)[0]*0.3)
    for u,v in HZ:
        d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;w/=np.linalg.norm(w)
        r.append(w[2]*p[6]*3)
    t=cKDTree(OD)
    for u,v in FB:
        d=np.array([(u-p[7])/p[6],-(v-p[8])/p[6],1.0]);w=M.T@d;s=-p[2]/w[2];X0=p[:3]+s*w
        r.append(t.query(X0[:2])[0]*3)
    return np.array(r)
q5=json.load(open('w/camPA6.json'));q0=np.r_[q5['q'],2.1]
lo=[-np.inf]*6+[200,0,0,0];hi=[np.inf]*6+[3000,W,H,22]
o=least_squares(res6,q0,loss='soft_l1',f_scale=2,max_nfev=2000,bounds=(lo,hi))
q=o.x;rr=res6(q);n=len(E);print('q',np.round(q,3),'cost',o.cost);d=rr[:n];print('edge rms',np.sqrt(np.mean(d**2)),'p90',np.percentile(d,90),'hz',np.round(rr[-11:-6]/3,1),'facade m',np.round(rr[-6:]/3,1))
json.dump({'q':q[:9].tolist(),'off':q[9]},open('w/camPA9.json','w'))
