import numpy as np, sys
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB'),float)
N=a.shape[0];half=1500
def box(x0,x1,y0,y1):
  i0=int((half-y1)/(2*half)*N);i1=int((half-y0)/(2*half)*N);j0=int((x0+half)/(2*half)*N);j1=int((x1+half)/(2*half)*N); return a[i0:i1,j0:j1]
for n,b in [('SW forest',(-700,-420,-400,50)),('stadium field',(-60,60,-60,60)),('golf NE',(150,250,450,600))]:
  s=box(*b);L=s.mean(2);exg=2*s[...,1]-s[...,0]-s[...,2]
  print(n,'L p10/50/90',np.percentile(L,[10,50,90]).round(),'exg p50',np.median(exg).round(),'lowLfrac',(L<55).mean().round(3))
