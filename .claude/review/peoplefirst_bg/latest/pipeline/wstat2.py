import numpy as np
from PIL import Image
from scipy import ndimage
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400), Image.BOX)).astype(float)
L=s.mean(2); sd=np.sqrt(np.clip(ndimage.uniform_filter(L**2,7)-ndimage.uniform_filter(L,7)**2,0,None))
gb=s[...,1]-s[...,2]
def box(x,y,r): m=np.zeros((1400,1400),bool); m[700-y-r:700-y+r,700+x-r:700+x+r]=True; return m
for n,(x,y,r) in {'pond0':(366,578,12),'pond6':(452,456,6),'river':(-100,520,15),'forestSW':(-560,-330,25),'golftrees':(606,250,8)}.items():
    m=box(x,y,r); print(n,'L',L[m].mean().round(1),'G-B',np.median(gb[m]),'sd',np.percentile(sd[m],[50,90]).round(1))
