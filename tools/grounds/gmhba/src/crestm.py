from PIL import Image
import numpy as np
for f in ('photo.jpg','ren.png'):
  a=np.array(Image.open(f).convert('RGB').crop((480,486,542,548))).astype(float)
  m=(a.sum(2)<330)&(a[...,2]>a[...,0]+10)      # navy
  ys,xs=np.nonzero(m)
  top=m[:,:].any(1);rows=np.nonzero(top)[0]
  print(f,'navy px',m.sum(),'x %.1f-%.1f'%(480+np.percentile(xs,2),480+np.percentile(xs,98)),'y %.1f-%.1f'%(486+np.percentile(ys,2),486+np.percentile(ys,98)),'centroid %.1f %.1f'%(480+xs.mean(),486+ys.mean()))
