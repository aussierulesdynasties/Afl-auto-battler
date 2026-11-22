import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
from skimage.segmentation import slic
from skimage.color import rgb2lab
K=int(sys.argv[1]); NS=int(sys.argv[2])
a=np.asarray(Image.open('_fc_sat.png').convert('RGB')).astype(np.float32)/255
lab=rgb2lab(a)
sp=slic(a,n_segments=NS,compactness=8,start_label=0)
n=sp.max()+1
m=np.stack([ndi.mean(lab[...,i],sp,range(n)) for i in range(3)],-1)
rgbm=np.stack([ndi.mean(a[...,i],sp,range(n)) for i in range(3)],-1)
L=rgbm.mean(1); pav=(L>0.42)&(L<0.9)&~(rgbm[:,1]>rgbm[:,0]*0.98)
f=m[pav]*np.array([0.5,1.5,1.5])
c,l=kmeans2(f,K,minit='++',seed=4)
cl=np.full(n,-1); cl[np.nonzero(pav)[0]]=l
P=cl[sp]
cols=[rgbm[np.nonzero(pav)[0][l==k]].mean(0) for k in range(K)]
print([np.round(x,3).tolist() for x in cols])
o=np.zeros(a.shape,np.uint8)
for k in range(K): o[P==k]=(cols[k]*255).astype(np.uint8)
Image.fromarray(np.hstack([(a*255).astype(np.uint8),o])).resize((1216,1016)).save('_slic.png')
np.save('_slic_P.npy',P)
