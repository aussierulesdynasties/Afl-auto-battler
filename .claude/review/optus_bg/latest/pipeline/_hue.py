import numpy as np
from PIL import Image
from scipy import ndimage as ndi
a=np.asarray(Image.open('_fc_sat.png').convert('RGB')).astype(np.float32)/255
a=ndi.uniform_filter(a,(3,3,1))
L=a.mean(2); h=a[...,0]-a[...,1]
pav=(L>0.45)&~((a[...,1]>a[...,0]))&(L<0.9)
print(np.histogram(h[pav],bins=np.arange(-0.02,0.3,0.02)))
for lo,hi in [(0.15,1),(0.08,0.15),(-1,0.08)]:
    m=pav&(h>=lo)&(h<hi); print(lo,hi,round(float(m.mean()),3),np.round(a[m].mean(0),3))
o=np.zeros(a.shape,np.uint8); o[pav&(h>=0.15)]=(200,120,110); o[pav&(h>=0.08)&(h<0.15)]=(220,200,170); o[pav&(h<0.08)]=(150,150,150)
Image.fromarray(np.hstack([(a*255).astype(np.uint8),o])).resize((1216,1016)).save('_hue.png')
