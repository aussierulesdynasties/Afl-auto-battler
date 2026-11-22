import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
K=int(sys.argv[1])
a=np.asarray(Image.open('_fc_sat.png').convert('RGB')).astype(np.float32)/255
b=ndi.gaussian_filter(a,(2,2,0))
L=b.mean(2)
pav=(L>0.42)&(L<0.88)&~((b[...,1]>b[...,0]*0.98))
f=np.dstack([b[...,0]-b[...,1], b[...,1]-b[...,2], L*0.5])
c,l=kmeans2(f[pav],K,minit='++',seed=3)
lab=np.full(L.shape,-1); lab[pav]=l
cols=[np.round(b[pav][l==k].mean(0),3).tolist() for k in range(K)]
print(cols,[round(float((l==k).mean()),2) for k in range(K)])
o=np.zeros(a.shape,np.uint8)
for k in range(K): o[lab==k]=(np.array(cols[k])*255).astype(np.uint8)
Image.fromarray(np.hstack([(a*255).astype(np.uint8),o])).resize((1216,1016)).save('_km.png')
np.save('_km_c.npy',c)
