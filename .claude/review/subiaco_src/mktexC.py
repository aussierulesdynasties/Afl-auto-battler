# hand-made procedural textures for the finished bowl (about 2000), no photo pixels: 512 px tiles
import numpy as np
from PIL import Image,ImageFilter
rng=np.random.default_rng(23);S=512;x=np.arange(S);y=np.arange(S)
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
def noise(blur=1):
    n=rng.normal(0,1,(S,S));return np.array(Image.fromarray(((n*20+128).clip(0,255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)),float)-128
# green plastic seats: 5 rows per 4 m tile, grey concrete step behind each row, pale aisle stair at the tile edge
s=np.full((S,S,3),[150,152,148.]);row=y%102
s[(row>12)&(row<62)]=[52,108,84];s[(row>=62)&(row<72)]=[30,64,52];s[:,0:20]=[214,214,208];s[:,20:24]=[150,152,148]
s+=noise(0.7)[...,None]*0.2;save(s,'seatsg')
# roof sheeting: pale silver-grey steel deck, standing seams every 0.5 m (tile 4 m), faint panel lap every 4 m
r=np.full((S,S,3),[214,218,226.]);r[:,(x%64)<5]=[186,190,200];r[(y%512)<4]=[176,180,190];r+=noise(1.5)[...,None]*0.12;save(r,'roofc')
# red-brown face brick, stretcher bond: 230x76 mm courses (tile 4 m)
b=np.full((S,S,3),[168,92,66.]);c=(y//10)%2;off=np.where(c[:,None]==1,15,0)
b[(y%10)<1]=[196,180,160];b[((x[None,:]+off)%30)<1]=[196,180,160]
b+=(rng.normal(0,9,(S//10+1,S//30+2))[(y//10)][:,((x[None,:]+off)//30)%(S//30+2)][...,None]*np.ones(3)).reshape(S,S,3) if False else 0
b+=noise(0.6)[...,None]*0.25;save(b,'brickr')
# bowl facade: white precast panels with a dark window band per 4 m storey, mullions every 2 m (tile 16 m)
f=np.full((S,S,3),[226,228,224.]);st=y%128;f[(st>58)&(st<92)]=[70,78,86.];f[(st>58)&(st<92)&((x%64)<3)[None,:].repeat(S,0)]=[200,202,198]
f[st<2]=[170,170,166];f+=noise(1)[...,None]*0.12;save(f,'facc')
# red forecourt pavers 1 m grid (tile 8 m)
p=np.full((S,S,3),[172,84,66.]);p[(y%64)<2]=[140,70,58];p[:,(x%64)<2]=[140,70,58];p+=noise(1)[...,None]*0.2;save(p,'pavr')
# roof underside seen from the field: dark steel purlins on grey
u=np.full((S,S,3),[84,86,92.]);u[(y%64)<6]=[60,62,68];u+=noise(1)[...,None]*0.1;save(u,'underc')
# east stand roof: dark grey steel deck, same seams as roofc (added after the first overlay)
r=np.full((S,S,3),[98,96,104.]);r[:,(x%64)<5]=[78,76,84];r[(y%512)<4]=[70,68,76];r+=noise(1.5)[...,None]*0.12;save(r,'roofk')
