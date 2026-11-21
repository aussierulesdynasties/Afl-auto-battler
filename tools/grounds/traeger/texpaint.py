# Hand-painted texture helpers (row 202 2b texture pass), rectangular version of the Marvel/Optus texpaint.
# No photo pixels: every mark is drawn from module sizes in metres. A Canvas covers tu x tv metres at the map's own
# pixel size (w x h); every helper wraps at the edges so tiled maps still tile. Row 0 is the TOP of the surface.
import numpy as np
from PIL import Image
class Canvas:
    def __init__(s,tu,tv,img,seed=1):
        s.a=np.asarray(img,float)[...,:3]/255.0;s.h,s.w=s.a.shape[:2];s.tu=tu;s.tv=tv;s.pu=s.w/tu;s.pv=s.h/tv
        s.R=np.random.default_rng(seed);s.col=s.a.reshape(-1,3).mean(0)
    def noise(s,scale_u,scale_v=None):
        scale_v=scale_u if scale_v is None else scale_v
        w=s.R.normal(size=(s.h,s.w));fy=np.fft.fftfreq(s.h)[:,None];fx=np.fft.fftfreq(s.w)[None,:]
        su,sv=max(scale_u*s.pu,0.5),max(scale_v*s.pv,0.5)
        g=np.exp(-2*np.pi**2*((fx*su)**2+(fy*sv)**2));r=np.real(np.fft.ifft2(np.fft.fft2(w)*g))
        return (r-r.mean())/(r.std()+1e-9)
    def mul(s,f):s.a*=np.asarray(f)[...,None] if np.ndim(f)==2 else f
    def mottle(s,amt,scales=(2.0,0.6,0.15),w=(1.0,0.6,0.35)):
        sc=[x for x in scales if x*min(s.pu,s.pv)>=1.0] or [scales[-1]]
        m=sum(wi*s.noise(x) for x,wi in zip(sc,w))/sum(w[:len(sc)]);s.mul(1+amt*m)
    def grain(s,amt):s.mul(1+amt*s.R.normal(size=(s.h,s.w)))
    def panels(s,pw,ph,joint=0.015,dark=0.55,tone=0.05,stagger=0.0):
        y,x=np.mgrid[0:s.h,0:s.w];um=x/s.pu;vm=y/s.pv
        row=np.floor(vm/ph).astype(int);off=(row*stagger*pw)%pw;col=np.floor(((um+off)%s.tu)/pw).astype(int)
        nr=int(np.ceil(s.tv/ph))+1;nc=int(np.ceil(s.tu/pw))+1;T=1+tone*s.R.normal(size=(nr,nc))
        s.mul(T[row%nr,col%nc])
        G=s.R.uniform(-1,1,size=(nr,nc,2))*tone*0.6;fu=((um+off)%pw)/pw-0.5;fv=(vm%ph)/ph-0.5
        s.mul(1+G[row%nr,col%nc,0]*fu+G[row%nr,col%nc,1]*fv)
        du=np.minimum((um+off)%pw,pw-(um+off)%pw);dv=np.minimum(vm%ph,ph-vm%ph);jw=max(joint,1.0/min(s.pu,s.pv))
        J=np.maximum(np.clip(1-du/jw,0,1),np.clip(1-dv/jw,0,1))**1.2;s.mul(1-(1-dark)*J)
    def streaks(s,ledges,per_m=1.2,length=(0.4,2.5),width=(0.03,0.25),amt=0.18,col=(0.35,0.33,0.30)):
        S=np.zeros((s.h,s.w))
        for y0 in ledges:
            for _ in range(max(1,int(per_m*s.tu))):
                x=s.R.uniform(0,s.tu);L=s.R.uniform(*length);w=s.R.uniform(*width);st=s.R.uniform(0.3,1.0)
                xs=np.arange(int((x-w*2)*s.pu),int((x+w*2)*s.pu)+1);ys=np.arange(int(y0*s.pv),int((y0+L)*s.pv)+1)
                if len(ys)<2 or len(xs)<1:continue
                fx=np.exp(-(((xs/s.pu)-x)/w)**2*2);t=(ys/s.pv-y0)/L;fy=(1-t)**1.6*np.clip(t*12,0,1)
                ix=np.ix_(ys%s.h,xs%s.w);S[ix]=np.maximum(S[ix],st*fy[:,None]*fx[None,:])
        S*=np.clip(1+0.5*s.noise(0.05,0.3),0,2);m=np.clip(S*amt,0,0.6)[...,None]
        c=np.array(col)*s.col.mean()/np.mean(col)*0.55;s.a=s.a*(1-m)+c*m
    def grime_bottom(s,h,amt=0.15,band=None,col=(0.30,0.28,0.25)):
        band=band or s.tv;y=np.mgrid[0:s.h,0:s.w][0]/s.pv;d=band-(y%band)
        g=np.clip(1-d/h,0,1)**1.8*np.clip(1+0.35*s.noise(0.8,0.25),0,2)*amt
        c=np.array(col)*s.col.mean()/np.mean(col)*0.6;s.a=s.a*(1-g[...,None])+c*g[...,None]
    def speckle(s,per_m2,size=(0.01,0.05),amt=0.2,light=False):
        M=np.zeros((s.h,s.w))
        for _ in range(int(per_m2*s.tu*s.tv)):
            cx,cy=s.R.uniform(0,s.w),s.R.uniform(0,s.h);r=s.R.uniform(*size);rx,ry=max(r*s.pu,.5),max(r*s.pv,.5)
            xs=np.arange(int(cx-rx*2),int(cx+rx*2)+1);ys=np.arange(int(cy-ry*2),int(cy+ry*2)+1)
            f=np.exp(-(((xs-cx)/rx)**2)[None,:]-(((ys-cy)/ry)**2)[:,None])*s.R.uniform(0.4,1)
            ix=np.ix_(ys%s.h,xs%s.w);M[ix]=np.maximum(M[ix],f)
        s.mul(1+amt*M if light else 1-amt*M)
    def hline(s,v,w,col,alpha=1.0):
        y=np.arange(s.h)/s.pv;d=np.abs(((y-v+s.tv/2)%s.tv)-s.tv/2);f=np.clip(1-d/max(w/2,0.5/s.pv),0,1)
        f=(f*alpha)[:,None,None];s.a=s.a*(1-f)+np.array(col)*f
    def vline(s,u,w,col,alpha=1.0):
        x=np.arange(s.w)/s.pu;d=np.abs(((x-u+s.tu/2)%s.tu)-s.tu/2);f=np.clip(1-d/max(w/2,0.5/s.pu),0,1)
        f=(f*alpha)[None,:,None];s.a=s.a*(1-f)+np.array(col)*f
    def keep_mean(s,target=None):
        t=s.col if target is None else np.array(target);s.a*=t/s.a.reshape(-1,3).mean(0)
def gstd(path):return float(np.asarray(Image.open(path).convert('L'),float).std())
