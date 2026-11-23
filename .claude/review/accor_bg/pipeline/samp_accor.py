from PIL import Image; import numpy as np
Image.MAX_IMAGE_PIXELS=None
im=np.asarray(Image.open('data/accor/sat.png').convert('RGB'),np.float32)
def m2p(x,y): return int(3000-y*2), int(3000+x*2)
for nm,(x,y) in {'plaza_n':(-20,260),'plaza_e':(160,120),'plaza_ne':(120,330),'pitch?':(0,0)}.items():
    i,j=m2p(x,y); print(nm, im[i-10:i+10,j-10:j+10].reshape(-1,3).mean(0).round())
