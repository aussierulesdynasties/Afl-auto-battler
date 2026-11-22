import sys, numpy as np
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB'),float); b=np.asarray(Image.open(sys.argv[2]).convert('RGB').resize((a.shape[1],a.shape[0])),float)
half=float(sys.argv[3]); H=a.shape[0]
def box(im,x0,x1,y0,y1):
    i0=int((half-y1)/(2*half)*H); i1=int((half-y0)/(2*half)*H); j0=int((x0+half)/(2*half)*H); j1=int((x1+half)/(2*half)*H); return im[i0:i1,j0:j1]
for nm,bb in [('yarra_park',(150,330,-80,120)),('fitzroy_gdns',(-450,-250,350,600))]:
    s=box(a,*bb); o=box(b,*bb)
    # canopy in sat: darker than local median grass by luminance
    L=s.mean(2); print(nm,'sat dark-frac',round(float((L<np.percentile(L,50)*0.8).mean()),2),'sat L p20/p80',np.percentile(L,[20,80]).round())
