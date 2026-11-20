# find aisle angles per seat tier: project points across the tier into the photo, mean saturation per angle, report dips
import numpy as np, math, sys, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import model as M
import cam
from PIL import Image
im=np.array(Image.open('photo.png').convert('HSV')).astype(float)
TIERS={'n_lower':(50,152,[(-0.5,1.3),(4.0,2.2)]),'n_upper':(57,152,[(8,3.8),(15,7.5)]),
       'w_lower':(190,237,[(1.5,1.5),(8.5,2.9)]),'w_upper':(190,237,[(12,4.0),(19,7.5)])}
for k,(t0,t1,(p0,p1)) in TIERS.items():
    A=np.arange(t0,t1,0.2);S=[];V=[]
    for t in A:
        a=math.radians(t);s=[];v=[]
        for f in np.linspace(0.1,0.9,7):
            d=p0[0]+f*(p1[0]-p0[0]);z=p0[1]+f*(p1[1]-p0[1]);x,y,zz=M.P(a,d,z);u,w=cam.proj([x,y,zz])[0]
            if 0<=u<1920 and 0<=w<1280:s.append(im[int(w),int(u),1]);v.append(im[int(w),int(u),2])
        S.append(np.mean(s) if s else np.nan)
    S=np.array(S);sm=np.convolve(np.nan_to_num(S,nan=np.nanmean(S)),np.ones(3)/3,'same')
    thr=np.nanmedian(sm)*0.6;dips=[]
    i=0
    while i<len(A):
        if sm[i]<thr:
            j=i
            while j<len(A) and sm[j]<thr:j+=1
            dips.append((round(A[i],1),round(A[j-1],1)));i=j
        else:i+=1
    print(k,'median sat',round(np.nanmedian(sm)),'aisles',dips)
