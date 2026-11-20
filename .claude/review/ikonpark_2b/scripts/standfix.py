# standfix.py IN OUT SAT KX KY W STAND[,STAND..]  -> move back/front vertices along the outward normal to the nearest
# strong satellite roof edge within +-W m (median-smoothed, 5-point averaged). Heights kept. Prints before/after.
import cv2,json,sys,numpy as np
G=json.load(open(sys.argv[1]));SAT=sys.argv[3];KX,KY,W=map(float,sys.argv[4:7]);names=sys.argv[7].split(',');UNI=len(sys.argv)>8
s=cv2.GaussianBlur(cv2.imread(SAT,0).astype(np.float32),(0,0),1.5);C=np.array(G['centre'][:2],float)
def val(x,y):return cv2.getRectSubPix(s,(1,1),(float((x+150)/0.25),float((230-y)/0.25)))[0,0]
def fit(P,sg):
  N=[];o=[];g=[];T=np.arange(-W,W+.01,0.25)
  for i in range(len(P)):
    a=P[max(i-1,0)][:2];b=P[min(i+1,len(P)-1)][:2];t=b-a;n=np.array([t[1],-t[0]]);n/=np.linalg.norm(n)
    if np.dot(n,P[i][:2]-C)<0:n=-n
    x,y,z=P[i];q=np.array([x+KX*z,y+KY*z]);pr=np.array([val(*(q+t*n)) for t in T]);d=np.gradient(pr)*-sg;j=int(np.argmax(d))
    N.append(n);o.append(T[j]);g.append(d[j])
  return np.array(o),np.array(g),np.array(N)
def rep(tag,o,g):print(f'  {tag} within2m {np.mean(abs(o)<=2):.2f} median {np.median(o):+.2f} p90|o| {np.percentile(abs(o),90):.2f}')
for nm in names:
  for key,sg in (('back',1),('front',-1)):
    P=np.array(G[nm][key],float);o,g,N=fit(P,sg);print(nm,key);rep('before',o,g)
    ok=g>=8;med=np.array([np.median(o[max(0,i-3):i+4][ok[max(0,i-3):i+4]]) if ok[max(0,i-3):i+4].any() else 0 for i in range(len(o))])
    if UNI:med[:]=np.median(o[ok])
    P[:,:2]+=med[:,None]*N;Q=P.copy()
    for i in range(2,len(P)-2):P[i,:2]=Q[i-2:i+3,:2].mean(0)
    o2,g2,_=fit(P,sg);rep('after ',o2,g2);G[nm][key]=P.round(2).tolist()
json.dump(G,open(sys.argv[2],'w',encoding='utf-8',newline=''))
