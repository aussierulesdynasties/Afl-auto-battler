# Fit each light tower's plan position: the mast is a bright vertical line; score candidate (x,y) by the brightness
# along its projected segment minus the brightness 4 px either side, summed over all views.
import sys,glob,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E,tri as T
import os;V=sorted(os.path.basename(p)[:-4] for p in glob.glob("ge/[ol][0-9][0-9][0-9].png"))
IM={v:cv2.cvtColor(cv2.imread(f'ge/{v}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32) for v in V}
TW={'T1':(-116.3,84.1),'T2':(6.2,139.1),'T3':(128.3,61.7),'T4':(120.5,-74.6),'T5':(-4.5,-134.5),'T6':(-124.6,-52.0)}
zs=np.linspace(float(sys.argv[1]) if len(sys.argv)>1 else 46,float(sys.argv[2]) if len(sys.argv)>2 else 58,25)
def score(x,y,per=False):
    out=[]
    for v in V:
        c=T.camv(v);P=np.array([E.proj(c,(x,y,z)) for z in zs]);d=P[-1]-P[0];n=np.array([-d[1],d[0]])/np.linalg.norm(d)
        if P[:,0].min()<5 or P[:,0].max()>1914 or P[:,1].min()<95 or P[:,1].max()>1035: continue
        s=lambda Q: cv2.remap(IM[v],Q[:,0:1].astype(np.float32),Q[:,1:2].astype(np.float32),cv2.INTER_LINEAR).mean()
        out.append(s(P)-0.5*(s(P+4*n)+s(P-4*n)))
    return out if per else (np.mean(out) if out else -1e9)
res={}
for k,(x0,y0) in TW.items():
    g=np.arange(-8,8.01,0.5);S=np.array([[score(x0+dx,y0+dy) for dx in g] for dy in g]);i,j=np.unravel_index(S.argmax(),S.shape)
    xb,yb=x0+g[j],y0+g[i];g2=np.arange(-0.6,0.61,0.1);S2=np.array([[score(xb+dx,yb+dy) for dx in g2] for dy in g2]);i,j=np.unravel_index(S2.argmax(),S2.shape)
    res[k]=(round(xb+g2[j],1),round(yb+g2[i],1));print(k,res[k],'score',round(S2.max(),1),'views',len(score(*res[k],per=True)),[round(s) for s in score(*res[k],per=True)])
