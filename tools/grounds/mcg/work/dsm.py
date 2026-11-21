# Plane-sweep surface model from the GE views: for each plan cell pick the height where the views agree best.
# python work/dsm.py out.npz res x0 y0 x1 y1 views...
import sys,cv2,numpy as np;sys.path.insert(0,'work');import earthcam as E,tri as T
out=sys.argv[1];res=float(sys.argv[2]);x0,y0,x1,y1=map(float,sys.argv[3:7]);V=sys.argv[7:]
xs=np.arange(x0,x1,res);ys=np.arange(y1,y0,-res);GX,GY=np.meshgrid(xs,ys)
IM={v:cv2.cvtColor(cv2.imread(f'ge/{v}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32) for v in V}
for v in V: IM[v][:90]=np.nan;IM[v][1040:]=np.nan
CC={v:T.camv(v) for v in V}
def warp(v,z):
    c=CC[v];D=np.stack([GX-c['C'][0],GY-c['C'][1],np.full_like(GX,z-c['C'][2])],-1);zc=D@c['fwd']
    u=c['W']/2+c['f']*(D@c['right'])/zc;w=c['H']/2-c['f']*(D@c['up'])/zc
    return cv2.remap(IM[v],u.astype(np.float32),w.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=np.nan)
k=int(__import__("os").environ.get("K","7"));K=(k,k)
def stats(a):
    m=cv2.boxFilter(a,-1,K);s=np.sqrt(np.maximum(cv2.boxFilter(a*a,-1,K)-m*m,1e-3));return m,s
zs=np.arange(-6,60,0.5);best=np.full(GX.shape,-2.0,np.float32);bz=np.zeros(GX.shape,np.float32);col=np.zeros(GX.shape,np.float32)
for z in zs:
    W=[warp(v,z) for v in V];S=np.stack(W);ok=~np.isnan(S);S0=np.nan_to_num(S)
    med=np.nanmedian(S,0);med=np.nan_to_num(med);mm,ms=stats(med)
    sc=[]
    for i in range(len(V)):
        a=S0[i];am,asd=stats(a);cov=cv2.boxFilter(a*med,-1,K)-am*mm;n=cov/(asd*ms)
        n[~ok[i]]=-1;sc.append(n)
    sc=np.sort(np.stack(sc),0)[-3:].mean(0)  # mean of the best 3 views
    upd=sc>best;best[upd]=sc[upd];bz[upd]=z;col[upd]=med[upd]
    print('z',z,flush=True) if z%10==0 else None
np.savez_compressed(out,z=bz,score=best,col=col,x0=x0,y1=y1,res=res)
