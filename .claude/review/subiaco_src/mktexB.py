# extra hand-made procedural textures for the 1997 ground (no photo pixels): 512 px tiles
import numpy as np
from PIL import Image,ImageFilter
rng=np.random.default_rng(11);S=512;x=np.arange(S);y=np.arange(S)
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
def noise(blur=1):
    n=rng.normal(0,1,(S,S));return np.array(Image.fromarray(((n*20+128).clip(0,255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)),float)-128
# blue plastic seats: rows every 0.8 m (tile 4 m -> 5 rows), white aisle stair every 4 m (one per tile edge)
s=np.full((S,S,3),[150,150,146.]);row=y%102
s[(row>14)&(row<60)]=[38,92,158];s[(row>=60)&(row<70)]=[24,58,104];s[:,0:22]=[226,226,220];s[:,22:26]=[150,150,146]
s+=noise(0.7)[...,None]*0.2;save(s,'seatsb')
# multi-storey concrete facade: 4 m storey = 1.3 m beige spandrel + 2.7 m dark glazing, mullions every 1.6 m
f=np.full((S,S,3),[48,52,58.]);st=y%128
f[st<42]=[196,184,160];f[st==42]=[150,140,120];f[(st>=42)&((x%51)<4)[None,:].repeat(S,0)&(st>=43)]=[120,116,108]
f+=noise(1)[...,None]*0.15;save(f,'facade')
# bare construction pad: pale concrete with saw-cut joints every 6 m (tile 12 m)
p=np.full((S,S,3),[214,212,204.]);p[(y%256)<3]=[184,182,174];p[:,(x%256)<3]=[184,182,174];p+=noise(1.2)[...,None]*0.2;save(p,'pad')
# grass bank (unmown, darker than the arena)
b=np.full((S,S,3),[66,96,50.])+noise(2)[...,None]*0.4;save(b,'bank')
# perimeter boards: plain coloured panels 3 m wide (tile 24 m -> 8 panels), white frame, no lettering
cols=[[236,236,230],[230,190,40],[200,40,36],[236,236,230],[240,140,30],[230,220,120],[40,80,160],[236,236,230]]
a=np.zeros((S,S,3))
for i,c in enumerate(cols):a[:,i*64:(i+1)*64]=c
a[:,(x%64)<3]=[90,90,90];a[:24]=[90,90,90];a[-24:]=[90,90,90];save(a,'ads')
# lamp head: dark steel frame holding 4 x 6 lamps (lit)
l=np.full((S,S,3),[60,62,66.])
for i in range(6):
    for j in range(4):
        cx,cy=40+i*86,64+j*128;yy,xx=np.ogrid[:S,:S];m=(xx-cx)**2+(yy-cy)**2<34**2;l[m]=[255,250,230]
save(l,'lamps')
# near bowl back: dark open concourse levels between pale concrete piers every 4 m (tile 16 m), floor slab every 8 m
k=np.full((S,S,3),[38,40,46.]);k[:,(x%128)<14]=[130,128,122];k[(y%256)<12]=[150,146,138];k+=noise(1)[...,None]*0.15;save(k,'facaded')
