import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=0.5;N=1500;x0,x1,y0,y1=90,242,-128,126
s=Image.open('data/optus/sat.png').convert('RGB').crop((int((x0+N)/R),int((N-y1)/R),int((x1+N)/R),int((N-y0)/R)))
a=np.asarray(s).astype(np.float32)/255
g=lambda x,sg:ndi.gaussian_filter(x,sg)
L=a.mean(2); rb=(a[...,0]-a[...,2])/(L+1e-3)
pav=(L>0.40)&~((a[...,1]>a[...,0])&(a[...,1]>a[...,2]))
w=pav.astype(np.float32)
lm=lambda x,sg:g(x*w,sg)/(g(w,sg)+1e-3)
sc=(g(L,0.8)-lm(L,12))*3-(g(rb,0.8)-lm(rb,12))
bei=(sc>0)&pav
bei=ndi.binary_opening(bei,iterations=1)
o=np.zeros(a.shape,np.uint8)+np.array([40,70,40],np.uint8)
o[pav]=(176,132,116); o[bei]=(206,190,170)
Image.fromarray(np.hstack([np.asarray(s),o])).resize((a.shape[1]*4,a.shape[0]*2)).crop((0,0,a.shape[1]*4,1000)).save('_two2.png')
np.save('_bei.npy',bei); np.save('_pav.npy',pav)
