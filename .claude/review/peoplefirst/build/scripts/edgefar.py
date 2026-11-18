import numpy as np
from PIL import Image
from roofedge import P
im=np.asarray(Image.open('photo_clean.png').convert('RGB')).astype(int)
for a in np.arange(300,396,6):
    s=''
    for dr in np.arange(6,-12,-1.0):
        u,v=P(a,dr);r,g,b=im[int(round(v)),int(round(u))]
        c='W' if min(r,g,b)>190 else ('Y' if r>170 and g>130 and b<110 else ('N' if b>r+10 and max(r,g,b)<170 else ('R' if r>g+50 else '.')))
        s+=c
    print(a,s)
