# hand-painted west stand back (refs back_west_2023, west_2019): brick base with arches, glazing strip,
# dark louvre band, open tier underside with white raking struts, light-grey panel fascia under the roof
import numpy as np
from PIL import Image
W,H=2048,2048; TU=36.0                       # one tile = 36 m along the curve (4 struts, 6 arches)
u=(np.arange(W)/W*TU)[None,:]*np.ones((H,1)); f=(1-np.arange(H)/H)[:,None]*np.ones((1,W))  # f: 0 ground .. 1 top
R=np.random.default_rng(7); img=np.zeros((H,W,3))
def put(m,c): img[m]=c
brick=np.array([0.62,0.30,0.22]); put(f<0.36,brick)
# brick courses: 86 mm courses at the wall's ~38 m height -> fraction
z=f*38; cr=(z%0.086)<0.012; bo=((u+np.floor(z/0.086)%2*0.115)%0.23)<0.012
img[(f<0.36)&(cr|bo)]=brick*1.25
tone=1+0.025*R.standard_normal((int(38/0.086)+2,int(TU/0.23)+2)); 
mb=f<0.36; zi=np.floor(z/0.086).astype(int); ui=np.floor(u/0.23).astype(int); img[mb]*=tone[zi,ui][mb][:,None]
# arches: 6 m pitch, 4.4 m wide, 6 m springing + semicircle
a=(u%6.0)-3.0; arch=(np.abs(a)<2.2)&((z<4.5)|(np.hypot(a,z-4.5)<2.2)); put(arch,np.array([0.10,0.10,0.11]))
ring=(np.abs(a)<2.55)&(np.hypot(a,z-4.5)<2.55)&(z>4.5)&~arch; img[ring]=brick*0.85
# cream string course and glazing strip
put((z>9.3)&(z<9.6),np.array([0.80,0.72,0.58]))
g=(z>10.6)&(z<12.6); put(g,np.array([0.30,0.36,0.42])); img[g&((u%1.5)<0.07)]=0.15
img[g&(z>11.6)]*=1.12
# dark louvre band
lb=(z>13.0)&(z<15.4); put(lb,np.array([0.17,0.18,0.20])); img[lb&((z%0.15)<0.04)]=0.12
# open tier underside: dark soffit with stepped tier lines, white raking struts every 9 m
ud=(z>=15.4)&(f<0.86); put(ud,np.array([0.24,0.25,0.27])); img[ud&((z%1.2)<0.12)]=0.32
for k in range(4):
    x0=k*9.0
    for s in (1,-1):
        t=(z-15.4)/(0.86*38-15.4); xc=x0+4.5+s*t*4.0
        img[ud&(np.abs(u-xc)<0.35)]=np.array([0.86,0.87,0.86])
img[ud&(np.abs((u%9.0)-4.5)<0.25)&(z<20)]=np.array([0.80,0.80,0.79])
# fascia: light grey vertical panels 1.2 m, shadow joint, white rail at the top
fa=f>=0.86; put(fa,np.array([0.74,0.76,0.78])); img[fa&((u%1.2)<0.05)]=np.array([0.55,0.57,0.60])
img[fa&(f>0.975)]=np.array([0.92,0.92,0.90]); img[fa&(f<0.875)]=np.array([0.40,0.41,0.43])
img*=(1+0.012*R.standard_normal((H,W)))[...,None]     # fine grain only, no mottle
AL=np.where(arch,0,255).astype(np.uint8)  # arches are real openings (alpha cut-out)
Image.fromarray(np.dstack([(np.clip(img,0,1)*255).astype(np.uint8),AL]),'RGBA').save(__import__('sys').argv[1])
