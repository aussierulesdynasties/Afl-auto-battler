import numpy as np
from PIL import Image
a=np.asarray(Image.open('data/traeger/sat.png').convert('RGB'),float); b=np.asarray(Image.open('out/traeger/ortho/top.png').convert('RGB'),float)
H=a.shape[0]; half=350
def s(im,x,y,r=6):
    i=int((half-y)/(2*half)*H); j=int((x+half)/(2*half)*H); return im[i-r:i+r,j-r:j+r].reshape(-1,3).mean(0)
for nm,x,y in [('oval',20,20),('oval2',-30,-30),('baseball_out',-170,60),('stuart_hwy',-195,150),('school_roof',170,320)]:
    print(nm,'sat',s(a,x,y).round(),'ours',s(b,x,y).round(),'ratio',(s(a,x,y)/s(b,x,y)).round(2))
