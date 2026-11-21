import sys,json,numpy as np;sys.path.insert(0,'work');import tri
from PIL import Image
def projv(c,X):
    d=X-c['C'];z=d@c['fwd'];return np.stack([c['W']/2+c['f']*(d@c['right'])/z,c['H']/2-c['f']*(d@c['up'])/z],-1)
R=np.arange(60,170,0.25);B=np.arange(0,360,1.0);Z=np.arange(20,56,1.0)
def edges(v):
    c=tri.camv(v);im=np.asarray(Image.open(f'ge/{v}.png').convert('RGB')).astype(float).mean(2)
    out=np.full((len(Z),len(B)),np.nan)
    for zi,z in enumerate(Z):
        a=np.radians(B)[:,None];X=np.stack([R[None]*np.sin(a),R[None]*np.cos(a),np.full((len(B),len(R)),z)],-1)
        P=projv(c,X);u=P[...,0].round().astype(int);w=P[...,1].round().astype(int)
        ok=(u>=0)&(u<1920)&(w>=90)&(w<1045);L=np.where(ok,im[np.clip(w,0,1079),np.clip(u,0,1919)],np.nan)
        K=np.ones(5)/5
        for bi in range(len(B)):
            l=np.convolve(np.nan_to_num(L[bi],nan=-999),K,'same');k=np.where((R>78)&(l<85)&(l>0))[0]
            if not len(k):continue
            for j in range(k[0],len(R)-12):
                if l[j:j+12].min()>120: out[zi,bi]=R[j];break
    return out
V=sys.argv[1:];E={v:edges(v) for v in V};np.savez('work/stereo.npz',**E)
ref=E[V[0]];res=[]
for bi,b in enumerate(B):
    best=[]
    for v in V[1:]:
        d=np.abs(ref[:,bi]-E[v][:,bi])
        if np.all(np.isnan(d)):continue
        zi=np.nanargmin(d)
        if d[zi]<0.75 and 0<zi<len(Z)-1: best.append((v,Z[zi],ref[zi,bi]))
    res.append([b,best])
json.dump([[b,[(v,float(z),float(r)) for v,z,r in bb]] for b,bb in res],open('work/stereo.json','w'))
for b,bb in res[::10]:print(b,[(v,z,round(r,1)) for v,z,r in bb])
