import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color
im=np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB'))
l=color.rgb2lab(ndi.gaussian_filter(im/255.,(2,2,0)))
for n,(c,r) in {'mulch1':(905,315),'mulch2':(1290,410),'mulch3':(760,330),'lawnpale':(660,320),'pave_beige':(900,500),'pave_salmon':(700,800),'pave_grey':(1000,830),'bedrim':(680,505)}.items():
  print(n,np.median(l[r-6:r+6,c-6:c+6].reshape(-1,3),0).round(1))
