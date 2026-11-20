# B (1997) textures from photo 17, hand-made (flat colours read as photo medians, no photo pixels):
# blue seats (photo 88,146,169), plain hoarding boards along the east pad's back (white/orange/yellow/red, no text), green bank.
import numpy as np
from PIL import Image, ImageFilter
rng=np.random.default_rng(7)
def nz(h,w,b=0.7):return np.array(Image.fromarray((rng.normal(0,1,(h,w))*20+128).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(b)),float)-128
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
y=np.arange(512)
s=np.full((512,1024,3),[92,96,94.]);row=(y%102)[:,None].repeat(1024,1)
s[(row>10)&(row<66)]=[70,128,152];s[(row>=66)&(row<78)]=[40,72,88]
s[:,0:40]=[178,180,174];s[:,40:44]=[96,100,98];s+=nz(512,1024)[...,None]*0.25;save(s,'seatsb7')
cols=[[236,234,226],[214,120,48],[226,190,70],[196,62,50],[236,234,226],[60,92,160],[226,190,70],[214,120,48]]
h=np.zeros((128,1024,3))
for i,c in enumerate(cols):h[:,i*128:(i+1)*128]=c
h[:,::128]=[40,40,40];h[:6]=[60,60,60];h[-6:]=[60,60,60];h+=nz(128,1024)[...,None]*0.2;save(h,'hoardb')
g=np.full((256,256,3),[85,92,40.])+nz(256,256,1.5)[...,None]*0.3;save(g,'bankg')
print('ok')
