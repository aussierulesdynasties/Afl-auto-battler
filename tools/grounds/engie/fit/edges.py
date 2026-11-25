# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json
P=json.load(open('profiles.json')); r0,r1,st=P['rs']; rs=np.arange(r0,r1,st)
GAPS=[(8,72),(135.4,141.4),(172.2,178.2),(205.8,211.8),(239.3,245.3),(272.3,278.3),(309.3,315.3)]
def ingap(b,m=1.5): return any(a-m<=b<=c+m for a,c in GAPS) or any(a-m<=b+360<=c+m for a,c in GAPS)
TH=150
pts=[]
for k,L in P['L'].items():
    b=float(k); L=np.array(L,float)
    if ingap(b) or np.isnan(L).mean()>0.2: continue
    L=np.nan_to_num(L,nan=0)
    br=L>TH; n=len(L); w=int(2/st)
    f=next((i for i in range(n-w) if rs[i]>65 and br[i:i+w].mean()>0.85),None)
    if f is None: continue
    e=next((i for i in range(f+w,n-w) if br[i:i+w].mean()<0.15),None)
    g=np.gradient(L)
    def ref(i,sign):
        a,c=max(0,i-int(3/st)),min(n,i+int(3/st)); j=a+np.argmax(sign*g[a:c]); return rs[j]
    rf=ref(f,1); rb=ref(e,-1) if e else None
    pts.append([b,rf,rb])
pts=np.array([[b,f,e if e else np.nan] for b,f,e in pts])
# outlier rejection against running median over 5 deg
def clean(col):
    keep=np.ones(len(pts),bool)
    for i,(b,*_) in enumerate(pts):
        d=np.abs(((pts[:,0]-b+180)%360)-180)<=2.5
        med=np.nanmedian(pts[d,col]); 
        if np.isnan(pts[i,col]) or abs(pts[i,col]-med)>2.0: keep[i]=False
    return keep
kf,kb=clean(1),clean(2)
json.dump({'rf':pts[kf][:,[0,1]].tolist(),'rb':pts[kb][:,[0,2]].tolist()},open('edges.json','w'))
print('rf pts',kf.sum(),'of',len(pts),' rb pts',kb.sum())
