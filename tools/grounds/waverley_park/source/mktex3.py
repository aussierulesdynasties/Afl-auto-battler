import numpy as np
from PIL import Image
rng=np.random.default_rng(11);O='tex2/'
def noise(h,w,sc,amp):   # seamless: the coarse grid wraps, so the tile repeats without a seam
    gh,gw=max(2,h//sc),max(2,w//sc);n=rng.normal(0,1,(gh,gw));t=np.tile(n,(3,3))
    im=Image.fromarray(((t-t.min())/(t.max()-t.min())*255).astype(np.uint8)).resize((3*w,3*h),Image.BICUBIC)
    return (np.asarray(im)[h:2*h,w:2*w]/255.0-0.5)*amp
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(O+n+'.png')
# bowl roof: light grey profiled sheet, ribs every 0.25 m (tile 4 m, 512 px)
h=w=512;r=np.ones((h,w,3))*np.array([178,179,183])+noise(h,w,64,8)[...,None]
for x in range(0,w,32):r[:,x:x+4]*=0.88;r[:,x+4:x+6]*=1.04
for y in range(0,h,256):r[y:y+3]*=0.82
save(r,'roofn');r=r*0.52
save(r,'roof')
# members' roof: same sheet, tile 2 m along the stand x 4 m, dark joint line every 2 m
h,w=512,256;r=np.ones((h,w,3))*np.array([122,108,110])+noise(h,w,32,8)[...,None]
for x in range(0,w,32):r[:,x:x+4]*=0.9
r[:,0:10]*=0.62
save(r,'roofm')
# dark roof rib (painted steel)
a=np.ones((32,32,3))*np.array([140,140,146])+rng.normal(0,2,(32,32,1));save(a,'rib')   # photo: near-roof ribs read faint grey
# concourse paving: grey asphalt/concrete with 4 m joints
h=w=512;a=np.ones((h,w,3))*np.array([128,127,123])+(noise(h,w,64,16)+noise(h,w,8,8)+rng.normal(0,4,(h,w)))[...,None]
a[0:3]*=0.75;a[:,0:3]*=0.75;save(a,'pave')
# embankment grass (mown, 1990s winter green-brown)
a=np.ones((h,w,3))*np.array([88,104,60])+(noise(h,w,64,22)+noise(h,w,6,14)+rng.normal(0,6,(h,w)))[...,None]*np.array([0.9,1.0,0.7])
save(a,'grass')
h=w=512
a=np.ones((h,w,3))*np.array([128,92,72])+(noise(h,w,64,26)+noise(h,w,6,12)+rng.normal(0,6,(h,w)))[...,None]*np.array([1.0,0.85,0.75]);save(a,'dirt')
a=np.ones((64,64,3))*np.array([226,128,44])+rng.normal(0,3,(64,64,1));a[:6]=[240,240,236];save(a,'kiosko')
a=np.ones((64,64,3))*np.array([44,84,112])+rng.normal(0,3,(64,64,1));a[:6]=[240,240,236];save(a,'kioskb')
a=np.ones((64,64,3))*np.array([40,128,64])+rng.normal(0,3,(64,64,1));a[:8]=[240,240,236];save(a,'greenpaint')
