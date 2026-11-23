import numpy as np
from PIL import Image
from scipy import ndimage
b=np.asarray(Image.open('data/peoplefirst/sat2.png').convert('RGB')).astype(float)
L=b.mean(2); sd=np.sqrt(np.clip(ndimage.uniform_filter(L**2,7)-ndimage.uniform_filter(L,7)**2,0,None))
for nm,(x,y) in [('river',(139,240)),('lake W',(-386,430)),('lake E',(387,151)),('creek',(-521,-645)),('pond',(-415,-649)),('forest shadow',(-686,-276)),('forest2',(-656,-349)),('golf grass',(-450,-600)),('road',(100,-200))]:
    px,py=x+700,700-y; r=slice(py-3,py+4),slice(px-3,px+4)
    print('%-14s RGB %s  G-B %.0f  sd %.1f'%(nm,b[r].reshape(-1,3).mean(0).round(),(b[r][...,1]-b[r][...,2]).mean(),np.median(sd[r])))
