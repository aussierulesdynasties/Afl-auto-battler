import numpy as np
from PIL import Image
from scipy import ndimage
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400), Image.BOX)).astype(float)
t0 = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)
L=s.mean(2); W1=(L<55)&(s[...,2]>=s[...,0]-4)
W2=ndimage.binary_erosion((t0[...,2]>t0[...,0]+25)&(t0[...,2]>t0[...,1]+5),iterations=4)
sd=np.sqrt(ndimage.uniform_filter(L**2,5)-ndimage.uniform_filter(L,5)**2)
def rep(n,m):
    print(n,m.sum(),'rgb',s[m].mean(0).round(1),'G-B',np.percentile(s[m][:,1]-s[m][:,2],[10,50,90]).round(1),'sd',np.percentile(sd[m],[10,50,90]).round(1))
rep('water',W1&W2)
rep('forest',W1&~ndimage.binary_dilation(W2,iterations=6))
