# edgefit.py GEOM STAND KEY SIGN [K DX DY]  -> per-vertex offset (m) along outward normal to the satellite roof edge
# SIGN +1: roof is bright on the inner side, dark outside (back edges). Prints offsets; writes ef_<stand>_<key>.png
import cv2,json,sys,numpy as np,os
G=json.load(open(sys.argv[1]));st,key,sg=sys.argv[2],sys.argv[3],int(sys.argv[4])
K,DX,DY=(float(v) for v in (sys.argv[5:8] if len(sys.argv)>7 else (0.5,0,1)))
s=cv2.imread(os.environ.get('SAT','sat/wb42663.png'),0).astype(np.float32);s=cv2.GaussianBlur(s,(0,0),1.5)
def val(x,y):
  c=(x+150)/0.25;r=(230-y)/0.25;return cv2.getRectSubPix(s,(1,1),(float(c),float(r)))[0,0]
P=np.array(G[st][key],float);C=np.array(G['centre'][:2],float)
T=np.arange(-8,8.01,0.25);res=[]
for i,(x,y,z) in enumerate(P):
  a=P[max(i-1,0)][:2];b=P[min(i+1,len(P)-1)][:2];t=b-a;n=np.array([t[1],-t[0]]);n/=np.linalg.norm(n)
  if np.dot(n,np.array([x,y])-C)<0:n=-n            # outward from the ground centre
  q=np.array([x+K*DX*z,y+K*DY*z])
  prof=np.array([val(*(q+tt*n)) for tt in T]);g=np.gradient(prof)*-sg   # bright->dark going outward = positive
  j=int(np.argmax(g));res.append((i,T[j],g[j]))
off=np.array([r[1] for r in res]);st_=np.array([r[2] for r in res])
print('n',len(off),'median',np.median(off),'mean',off.mean().round(2),'p10/p90',np.percentile(off,[10,90]).round(2))
print(' '.join(f'{o:+.1f}' for o in off))
print('strength',' '.join(f'{v:.0f}' for v in st_))
