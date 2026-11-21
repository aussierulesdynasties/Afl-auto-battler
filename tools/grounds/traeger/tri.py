# python tri.py camA camB uA,vA,uB,vB ... -> s,t,z by triangulation (closest point of two rays)
import sys,json,numpy as np,cv2,stand
def ray(f,u,v):
    c=json.load(open(f));R=cv2.Rodrigues(np.array(c['r']))[0];C=-R.T@np.array(c['t'])
    K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1]]);d=R.T@np.linalg.inv(K)@[u,v,1];return C,d/np.linalg.norm(d)
for q in sys.argv[3:]:
    uA,vA,uB,vB=map(float,q.split(','));C1,d1=ray(sys.argv[1],uA,vA);C2,d2=ray(sys.argv[2],uB,vB)
    A=np.array([[d1@d1,-d1@d2],[d1@d2,-d2@d2]]);bb=np.array([(C2-C1)@d1,(C2-C1)@d2]);l1,l2=np.linalg.solve(A,bb)
    X=(C1+l1*d1+C2+l2*d2)/2;gap=np.linalg.norm(C1+l1*d1-C2-l2*d2);rel=X[:2]-stand.O
    print(q,'s=%.2f t=%.2f z=%.2f gap=%.2f'%(rel@stand.a,rel@stand.b,X[2],gap))
