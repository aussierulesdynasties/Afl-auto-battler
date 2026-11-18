# hand-made procedural textures (no photo pixels): 512 px tiles
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
rng=np.random.default_rng(7);S=512
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
def noise(s=1.0,blur=1):
    n=rng.normal(0,1,(S,S));return np.array(Image.fromarray(((n*20+128).clip(0,255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)),float)-128
# turf: mown stripes 8 m (tile = 32 m -> 4 stripes)
t=np.zeros((S,S,3));base=np.array([86,128,58.]);x=np.arange(S)
stripe=np.where((x//64)%2==0,1.0,0.88)[None,:,None]
t[:]=base;t=t*stripe+noise(1,1.2)[...,None]*0.35;save(t,'turf')
# white marking
save(np.full((8,8,3),240.),'paint')
# concrete terrace steps: 0.4 m treads, tile 4 m -> 10 steps, riser shadow line
c=np.full((S,S,3),[178,174,166.]);y=np.arange(S)
c*= (1-0.18*((y%51)<6))[:,None,None];c+=noise(1,0.8)[...,None]*0.25;save(c,'terrace')
# bench seats: dark green timber benches on concrete, rows every 0.8 m (tile 4 m -> 5 rows)
s=np.full((S,S,3),[160,156,148.]);row=(y%102)
s[(row>20)&(row<46)]=[52,84,62];s[(row>=46)&(row<54)]=[34,52,40];s+=noise(1,0.7)[...,None]*0.2;save(s,'seats')
# roof sheeting: off-white corrugated, ribs every 0.25 m (tile 4 m -> 16 ribs)
r=np.full((S,S,3),[226,220,206.]);rib=np.cos(x/32*2*np.pi)[None,:,None];r=r+rib*9+noise(1,1)[...,None]*0.12;save(r,'roof')
# ribbed dark roof: grey steel decking, ribs every 0.6 m
d=np.full((S,S,3),[118,118,114.]);rib=np.where((x%77)<10,-26,0)[None,:,None]+np.where((x%77)>70,14,0)[None,:,None];d=d+rib+noise(1,1)[...,None]*0.15;save(d,'roofd')
# white painted render wall with faint panel joints every 4 m
w=np.full((S,S,3),[236,232,222.]);w[:,0:3]=[205,200,190];w[0:3,:]=[214,210,200];w+=noise(1,1.5)[...,None]*0.12;save(w,'wall')
# cream brick wall (old stand backs)
b=np.full((S,S,3),[214,196,164.]);
for yy in range(0,S,16):
    b[yy:yy+2]=[190,182,170];off=0 if (yy//16)%2==0 else 32
    for xx in range(off,S,64):b[yy:yy+16,xx:xx+2]=[190,182,170]
b+=noise(1,0.6)[...,None]*0.3;save(b,'brick')
# under-roof soffit / shadowed concourse
save(np.full((S,S,3),[92,90,86.])+noise(1,2)[...,None]*0.1,'under')
# white fascia and rails
save(np.full((S,S,3),[246,244,238.])+noise(1,2)[...,None]*0.05,'fascia')
# asphalt and paving
save(np.full((S,S,3),[96,96,94.])+noise(1,0.7)[...,None]*0.25,'asphalt')
p=np.full((S,S,3),[214,196,160.]);p[(y%64)<3]=[190,174,140];p[:,(x%64)<3]=[190,174,140];p+=noise(1,0.7)[...,None]*0.2;save(p,'paving')
# picket fence: white boards with gaps
f=np.full((S,S,3),[244,242,236.]);f[:,(x%32)<6]=[70,90,60];save(f,'picket')
# steel pole (galvanised)
save(np.full((S,S,3),[176,178,176.])+noise(1,3)[...,None]*0.1,'steel')
# light-yellow can (Swan Lager style generic can colours, no brand): gold with red band
cn=np.full((S,S,3),[214,170,60.]);cn[200:300]=[180,30,30];save(cn,'can')
# glass windows band: dark glass panes in white frames
g=np.full((S,S,3),[60,74,86.]);g[:,(x%64)<6]=[230,228,220];g[(y%128)<6]=[230,228,220];save(g,'glass')
# terracotta roof (houses-style tiles for small sheds)
tr=np.full((S,S,3),[170,84,56.]);tr[(y%32)<4]=[130,60,40];save(tr,'tiles')
print('ok')
