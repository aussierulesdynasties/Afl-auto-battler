# Run from a work folder holding the Google Earth shots in ge/ (never committed; looking and measuring only).
import numpy as np, json, math, cv2
C=json.load(open('cal.json')); S,DX,DY=C['s'],C['dx'],C['dy']; FIT=json.load(open('fit.json')); p=np.array(FIT['p']); K=FIT['K']
im=cv2.imread('ge/top3000.png').astype(int); red=(im[...,2]>im[...,1]+45)&(im[...,2]>110)
def rr(t): return p[2]+sum(p[2+2*k-1]*np.cos(k*t)+p[2+2*k]*np.sin(k*t) for k in range(1,K+1))
out=[]
for b in np.arange(20,240,1.0):
    t=math.radians(b); r=rr(t)
    for dd in np.arange(-2,12,0.25):
        e=p[0]+(r+dd)*math.sin(t); n=p[1]+(r+dd)*math.cos(t)
        x=int(round(640+(e-DX)/S)); y=int(round(360-(n-DY)/S))
        if 0<=x<1280 and 0<=y<720 and red[max(0,y-1):y+2,max(0,x-1):x+2].mean()>0.6:
            out.append((b,dd)); break
a=np.array(out)
for a0,a1 in ((20,72),(77,135),(141,172),(178,206),(212,239)):
    m=(a[:,0]>=a0)&(a[:,0]<=a1); print(a0,a1,'n',m.sum(),'median gap grass->first red seats %.2f m (p25 %.2f p75 %.2f)'%(np.median(a[m,1]),np.percentile(a[m,1],25),np.percentile(a[m,1],75)))
