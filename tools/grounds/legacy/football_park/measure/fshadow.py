# fshadow.py IMG A0 A1 OUT.json : roof front height from the roof's shadow on the turf, walking along the sun-minus-lean line
# env: CX CY MPP (field centre, scale), S=sx,sy and L=lx,ly in px per metre of height, FIT (fence fit json), LIT (lit turf threshold)
import sys,os,cv2,json,numpy as np
IMG=sys.argv[1];A0,A1=float(sys.argv[2]),float(sys.argv[3]);OUT=sys.argv[4]
cx,cy,S=float(os.environ['CX']),float(os.environ['CY']),float(os.environ['MPP'])
s=np.array([float(v) for v in os.environ['S'].split(',')]);l=np.array([float(v) for v in os.environ['L'].split(',')])
f=json.load(open(os.environ['FIT']));K=f['K'];c=np.array(f['c'])
def fr(a):
    t=np.radians(a);return float(np.concatenate([[1],[g(k*t) for k in range(1,K+1) for g in (np.cos,np.sin)]])@c)
img=cv2.imread(IMG).astype(np.float32);g=cv2.GaussianBlur(img.mean(2),(0,0),1.0);G=cv2.GaussianBlur(img[...,1]-img[...,2],(0,0),1.0)
LIT=float(os.environ.get('LIT','45'));ROOF=float(os.environ.get('ROOF','170'))
d=s-l;k=np.linalg.norm(d);u=-d/k;print('|s-l| %.3f px/m, u'%k,u)
res=[]
for a in np.arange(A0,A1+0.01,2.0):
    t=np.radians(a);r=fr(a);F=np.array([cx+r*np.cos(t)/S,cy-r*np.sin(t)/S])
    ts=np.arange(-150,300,0.5);P=F[None]+ts[:,None]*u[None]
    v=cv2.remap(g,P[:,0].astype(np.float32)[None],P[:,1].astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    Gv=cv2.remap(G,P[:,0].astype(np.float32)[None],P[:,1].astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    br=v>ROOF;iE=None
    for i in range(len(ts)-12):
        if ts[i]>0 and br[i:i+12].all(): iE=i;break
    if iE is None: continue
    lit=(v>LIT)&(Gv>4);iS=None
    for i in range(iE-1,25,-1):
        if ts[i]<10 and lit[i-24:i].all(): iS=i;break
    if iS is None: continue
    h=(ts[iE]-ts[iS])/k
    res.append((float(a),float(ts[iS]),float(ts[iE]),float(h),P[iS].tolist(),P[iE].tolist()))
for r in res: print('%5.0f  shadow t %6.1f  roof t %6.1f  h %.1f'%r[:4])
json.dump(res,open(OUT,'w'))
