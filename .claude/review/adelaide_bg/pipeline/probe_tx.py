import sys
from PIL import Image
import numpy as np
for p in sys.argv[1:]:
    im=Image.open(p); a=np.asarray(im.convert('RGBA')).astype(float)/255
    lin=np.where(a[...,:3]<=0.04045,a[...,:3]/12.92,((a[...,:3]+0.055)/1.055)**2.4)
    print(p.split('/')[-1], im.mode, im.size, 'alpha', a[...,3].min(), a[...,3].max(), 'lin mean', lin.reshape(-1,3).mean(0).round(3))
