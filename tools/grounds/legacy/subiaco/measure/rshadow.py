# eshadow.py : east roof front height from frame 52 (satellite, winter morning): shadow edge on the turf vs roof edge,
# both measured along the sun-minus-lean direction; sun and lean from the NE tower (65 m)
import sys,cv2,numpy as np,json
sys.path.insert(0,'/home/user/work/subi/photo'); from camsolve import fr
IMG=sys.argv[1]; img=cv2.imread(IMG).astype(np.float32); g=cv2.GaussianBlur(img.mean(2),(0,0),1.0)
G=cv2.GaussianBlur(img[...,1]-img[...,2],(0,0),1.0)   # green minus red: turf
if IMG.endswith('hist_14.png'):
    s=np.array([-0.527,4.295]); l=np.array([0.109,-0.044])
else:
    B=np.array([1136.2,733.0]); Hi=np.array([1243,636.0]); Hs=np.array([980,1040.0]); l=(Hi-B)/65; s=(Hs-B)/65
d=s-l; k=np.linalg.norm(d); u=-d/k
print('l',l,'s',s,'|s-l| px/m',k)
S=0.2945; res=[]
A0,A1=float(sys.argv[2]),float(sys.argv[3]); LIT=float(sys.argv[4]) if len(sys.argv)>4 else 17
for a in np.arange(A0,A1+0.5,2.0):
    t=np.radians(a); r=fr(np.array([a]))[0]; F=np.array([941+r*np.cos(t)/S,1021-r*np.sin(t)/S])
    ts=np.arange(-150,260,0.5); P=F[None]+ts[:,None]*u[None]
    v=cv2.remap(g,P[:,0].astype(np.float32)[None],P[:,1].astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    # roof: first run of bright (>150) lasting 3 m+ beyond the fence side
    Gv=cv2.remap(G,P[:,0].astype(np.float32)[None],P[:,1].astype(np.float32)[None],cv2.INTER_LINEAR)[0]
    br=v>150; iE=None
    for i in range(len(ts)-20):
        if br[i:i+20].all() and ts[i]>-20: iE=i; break
    if iE is None: continue
    # shadow edge: walking back from the roof edge toward the field, the first lit-turf sample (value>45 for 6 samples)
    lit=(v>LIT)&(v<LIT+80)&(Gv>4); iS=None
    for i in range(iE-1,25,-1):
        if ts[i]<15 and lit[i-24:i].all(): iS=i; break
    if iS is None: continue
    h=(ts[iE]-ts[iS])/k
    res.append((float(a),float(ts[iS]),float(ts[iE]),float(h),P[iS].tolist(),P[iE].tolist()))
for r in res: print('%5.0f  shadow t %6.1f  roof t %6.1f  h %.1f'%r[:4])
json.dump(res,open(sys.argv[5] if len(sys.argv)>5 else 'z/eshadow.json','w'))
