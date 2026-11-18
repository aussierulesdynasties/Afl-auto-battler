import json,math,numpy as np
from PIL import Image
from roofedge import P,D
im=np.asarray(Image.open('photo_clean.png').convert('RGB')).astype(int)
def px(u,v):return im[int(round(v)),int(round(u))]
out=[]
for a in np.arange(126,262,4):
    # walk outward from 14 m inside rin, find first navy pixel (b>r+15, b>g, value<170)
    hit=None
    for dr in np.arange(-14,6,0.25):
        u,v=P(a,dr);r,g,b=px(u,v)
        if b>r+15 and b>g+5 and max(r,g,b)<175:hit=dr;break
    out.append((a,hit))
print(' '.join(f'{a:.0f}:{h}' for a,h in out))
