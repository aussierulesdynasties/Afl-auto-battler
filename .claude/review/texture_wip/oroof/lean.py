import numpy as np
from PIL import Image
S=np.asarray(Image.open('../obuild/sat/sat_025.png').convert('RGB')).astype(int)
W=(S.min(2)>185)&(S.max(2)-S.min(2)<40);M=np.asarray(Image.open('top_mask.png').convert('L'))>128
best=None
for dy in range(-80,81,2):
    for dx in range(-80,81,2):
        Ms=np.roll(np.roll(M,dy,0),dx,1);i=(Ms&W).sum();u=(Ms|W)[300:1600,300:1700].sum()
        s=i/Ms.sum()
        if best is None or s>best[0]:best=(s,dx,dy)
print(best)
