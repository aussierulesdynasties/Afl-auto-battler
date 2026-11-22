# hand-painted fin cladding, 1024px = 8 m (128 px/m), from Populous Gate 1 photo
import numpy as np
from PIL import Image
R=np.random.default_rng(7);N=1024;img=np.zeros((N,N,3))
gap=np.array([70,76,84.]);x=0
while x<N:
    w=int(R.choice([38,52,64,77]));g=int(R.choice([10,14,18]))
    tone=R.choice([236,226,214])+R.uniform(-3,3);col=np.array([tone,tone+1,tone+3])
    img[:,x:x+w]=col
    img[:,x:x+w//6]=col*0.88          # fold shading on fin edge
    img[:,x+w:x+w+g]=gap;x+=w+g
# floor slab lines every 4 m (dark band 0.35 m) and a recessed window strip on one floor
for y0 in (0,512):
    img[y0:y0+45]=np.array([92,96,104.])
img[300:420:,:]=img[300:420]*0.55+np.array([60,72,86.])*0.45
img+=R.normal(0,1.2,(N,N,1))
Image.fromarray(np.clip(img,0,255).astype(np.uint8)[::-1]).save('v2/wall.png')
