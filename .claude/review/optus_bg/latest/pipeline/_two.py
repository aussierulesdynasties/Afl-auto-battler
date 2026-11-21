import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=0.5;N=1500;x0,x1,y0,y1=90,242,-128,126
s=Image.open('data/optus/sat.png').convert('RGB').crop((int((x0+N)/R),int((N-y1)/R),int((x1+N)/R),int((N-y0)/R)))
a=np.asarray(s).astype(np.float32)/255
rb=ndi.gaussian_filter(a[...,0]-a[...,2],1.0); L=ndi.gaussian_filter(a.mean(2),1.0)
pav=(L>0.45)&~((a[...,1]>a[...,0])&(a[...,1]>a[...,2]))
for t in (0.10,0.13,0.16): print(t, ((rb>t)&pav).sum()/pav.sum())
sal=(rb>0.13)&pav; bei=(rb<=0.13)&pav
sal=ndi.binary_opening(sal,iterations=1); 
o=np.zeros(a.shape,np.uint8)+np.array([40,70,40],np.uint8)
o[bei]=(206,190,170); o[sal]=(176,132,116)
Image.fromarray(np.hstack([np.asarray(s),o])).resize((a.shape[1]*4,a.shape[0]*2)).save('_two.png')
print('beige pieces',ndi.label(ndi.binary_opening(bei,iterations=2))[1])
