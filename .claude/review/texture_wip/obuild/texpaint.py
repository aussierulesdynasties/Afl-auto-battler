# Hand-painted tiling texture helpers (row 202 2b texture pass). No photo pixels: every mark is drawn from
# measured module sizes in metres. A Canvas covers tu x tv metres (one texture repeat); every helper wraps at
# the edges so the map tiles. Image row 0 is the TOP of the surface (walls: v = height, so streaks run down).
import numpy as np
from PIL import Image
N=1024
class Canvas:
    def __init__(s,tu,tv,col,seed=1,n=N):
        s.n=n;s.tu=tu;s.tv=tv;s.pu=n/tu;s.pv=n/tv;s.R=np.random.default_rng(seed)
        s.col=np.array(col,float);s.a=np.ones((n,n,3))*s.col
    # ---- tileable gaussian-filtered noise (unit std), scale in metres; aniso stretches along u or v
    def noise(s,scale_u,scale_v=None):
        scale_v=scale_u if scale_v is None else scale_v
        w=s.R.normal(size=(s.n,s.n));fy=np.fft.fftfreq(s.n)[:,None];fx=np.fft.fftfreq(s.n)[None,:]
        su,sv=max(scale_u*s.pu,0.5),max(scale_v*s.pv,0.5)
        g=np.exp(-2*np.pi**2*((fx*su)**2+(fy*sv)**2))
        r=np.real(np.fft.ifft2(np.fft.fft2(w)*g));return (r-r.mean())/(r.std()+1e-9)
    def mul(s,f):s.a*=np.asarray(f)[...,None] if np.ndim(f)==2 else f
    def mottle(s,amt,scales=(2.0,0.6,0.15),w=(1.0,0.6,0.35)):
        m=sum(wi*s.noise(sc) for sc,wi in zip(scales,w))/sum(w);s.mul(1+amt*m)
    def grain(s,amt):s.mul(1+amt*s.R.normal(size=(s.n,s.n)))
    def tint(s,amt,scale=1.5,toward=(0.9,0.85,0.75)):
        m=np.clip(s.noise(scale)*0.5+0.5,0,1)*amt;s.a=s.a*(1-m[...,None])+np.array(toward)*s.col.mean()/np.mean(toward)*m[...,None]
    # ---- panel grid: per-panel tone (blotching between panels), dark joint + light lip under it
    def panels(s,pw,ph,joint=0.015,dark=0.55,tone=0.05,stagger=0.0,lip=0.6,bevel=True):
        y,x=np.mgrid[0:s.n,0:s.n];um=x/s.pu;vm=y/s.pv
        row=np.floor(vm/ph).astype(int);off=(row*stagger*pw)%pw
        col=np.floor(((um+off)%s.tu)/pw).astype(int)
        nr=int(np.ceil(s.tv/ph));nc=int(np.ceil(s.tu/pw))+1;T=1+tone*s.R.normal(size=(nr+1,nc+1))
        s.mul(T[row%(nr+1),col%(nc+1)])
        # within-panel soft gradient (one corner lighter) so panels read as separate sheets
        G=s.R.uniform(-1,1,size=(nr+1,nc+1,2))*tone*0.6;fu=((um+off)%pw)/pw-0.5;fv=(vm%ph)/ph-0.5
        s.mul(1+G[row%(nr+1),col%(nc+1),0]*fu+G[row%(nr+1),col%(nc+1),1]*fv)
        du=np.minimum(((um+off)%pw),pw-((um+off)%pw));dv=vm%ph
        jw=joint
        J=np.clip(1-du/jw,0,1)**1.2;J=np.maximum(J,np.clip(1-np.minimum(dv,ph-dv)/jw,0,1)**1.2)
        s.mul(1-(1-dark)*J)
        if bevel:  # light lip just below each horizontal joint (top edge of the panel catches sky)
            L=np.clip(1-np.abs(dv-jw*1.6)/(jw*0.8),0,1);s.mul(1+lip*0.25*L)
        return row,col
    # ---- rain streaks: start under each ledge line (metres from the top of the repeat), run down
    def streaks(s,ledges,per_m=1.2,length=(0.4,2.5),width=(0.03,0.25),amt=0.18,col=(0.35,0.33,0.30)):
        S=np.zeros((s.n,s.n))
        for y0 in ledges:
            k=int(per_m*s.tu)
            for _ in range(k):
                x=s.R.uniform(0,s.tu);L=s.R.uniform(*length);w=s.R.uniform(*width);st=s.R.uniform(0.3,1.0)
                xs=np.arange(int((x-w*2)*s.pu),int((x+w*2)*s.pu)+1);ys=np.arange(int(y0*s.pv),int((y0+L)*s.pv)+1)
                if len(ys)<2:continue
                fx=np.exp(-(((xs/s.pu)-x)/w)**2*2)
                t=(ys/s.pv-y0)/L;fy=(1-t)**1.6*np.clip(t*12,0,1)
                S[np.ix_(ys%s.n,xs%s.n)]=np.maximum(S[np.ix_(ys%s.n,xs%s.n)],st*fy[:,None]*fx[None,:])
        S*=np.clip(1+0.5*s.noise(0.05,0.3),0,2)
        m=np.clip(S*amt,0,0.6)[...,None];c=np.array(col)*s.col.mean()/np.mean(col)*0.55
        s.a=s.a*(1-m)+c*m
    # ---- grime band: darker toward the bottom of each repeat (or each band of height h)
    def grime_bottom(s,h,amt=0.15,band=None,col=(0.30,0.28,0.25)):
        band=band or s.tv;y=np.mgrid[0:s.n,0:s.n][0]/s.pv;d=band-(y%band)
        g=np.clip(1-d/h,0,1)**1.8*np.clip(1+0.35*s.noise(0.8,0.25),0,2)*amt
        c=np.array(col)*s.col.mean()/np.mean(col)*0.6;s.a=s.a*(1-g[...,None])+c*g[...,None]
    # ---- wear spots / scuffs
    def speckle(s,per_m2,size=(0.01,0.05),amt=0.2,light=False):
        k=int(per_m2*s.tu*s.tv);y,x=np.ogrid[0:s.n,0:s.n]
        M=np.zeros((s.n,s.n))
        for _ in range(k):
            cx,cy=s.R.uniform(0,s.n,2);r=s.R.uniform(*size)
            rx,ry=r*s.pu,r*s.pv;x0,x1=int(cx-rx*2),int(cx+rx*2)+1;y0,y1=int(cy-ry*2),int(cy+ry*2)+1
            xs=np.arange(x0,x1);ys=np.arange(y0,y1)
            f=np.exp(-(((xs-cx)/max(rx,.5))**2)[None,:]-(((ys-cy)/max(ry,.5))**2)[:,None])*s.R.uniform(0.4,1)
            M[np.ix_(ys%s.n,xs%s.n)]=np.maximum(M[np.ix_(ys%s.n,xs%s.n)],f)
        s.mul(1+amt*M if light else 1-amt*M)
    # ---- lines in metres
    def hline(s,v,w,col,alpha=1.0,soft=True):
        y=np.arange(s.n)/s.pv;d=np.abs(((y-v+s.tv/2)%s.tv)-s.tv/2)
        f=np.clip(1-d/max(w/2,0.5/s.pv),0,1) if soft else (d<=w/2).astype(float)
        f=(f*alpha)[:,None,None];s.a=s.a*(1-f)+np.array(col)*f
    def vline(s,u,w,col,alpha=1.0,soft=True):
        x=np.arange(s.n)/s.pu;d=np.abs(((x-u+s.tu/2)%s.tu)-s.tu/2)
        f=np.clip(1-d/max(w/2,0.5/s.pu),0,1) if soft else (d<=w/2).astype(float)
        f=(f*alpha)[None,:,None];s.a=s.a*(1-f)+np.array(col)*f
    def keep_mean(s,target=None):
        t=s.col if target is None else np.array(target);m=s.a.reshape(-1,3).mean(0);s.a*=t/m
    def img(s):return np.clip(s.a,0,1)
def save(a,path):Image.fromarray((np.clip(a,0,1)*255+0.5).astype(np.uint8)).save(path)
def gstd(path):return float(np.asarray(Image.open(path).convert('L'),float).std())
