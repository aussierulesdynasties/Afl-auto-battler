# WACA hand repaints over tex.py output (no photo pixels). python paint_tex.py tex
# glass: 1990s tinted glazing reads as sky-reflecting panes, not flat black: per-pane tone, a soft sky
# gradient (lighter at the top of each pane), grey aluminium mullions. white/concrete: even painted
# render, faint rain streaks under each 3 m joint (kept low; director: no blotchy mottle).
import sys,os,json,numpy as np
from PIL import Image,ImageFilter
d=sys.argv[1];N=1024;R=np.random.default_rng(11)
def px(m,s):return int(round(m*N/s))
# glass, 6 m tile, 1.5 m bays, transoms at 0,1.1,3,4.1 m
s=6.0;y,x=np.mgrid[0:N,0:N]/N*s;img=np.zeros((N,N,3))
bay=np.floor(x/1.5).astype(int);rows=np.digitize(y,[1.1,3,4.1])
tone=R.normal(0,6,(4,4))[bay%4,rows%4]
zt=np.choose(rows,[y-0,y-1.1,y-3,y-4.1]);ph=np.choose(rows,[1.1,1.9,1.1,1.9])
g=np.clip(zt/ph,0,1)
base=np.array([52,62,80]);sky=np.array([96,112,132])
for k in range(3):img[...,k]=base[k]+(sky[k]-base[k])*(1-g)**1.5*0.8+tone
m=np.zeros((N,N),bool)
for k in range(5):m[:,px(k*1.5,s):px(k*1.5,s)+5]=True
for z in(0,1.1,3,4.1):m[px(z,s):px(z,s)+5,:]=True
img[m]=(150,152,158)
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8))
for nm in('glass','dark'):im.save(f'{d}/{nm}.png')
print('glass sd %.1f'%img.mean(2).std())
def render(nm,rgb,s=6.0,joint=3.0):
    y,x=np.mgrid[0:N,0:N]/N*s;img=np.ones((N,N,3))*rgb
    st=np.zeros((N,N));cols=R.random(N)
    for c in np.where(cols>0.93)[0]:
        L=R.uniform(0.4,1.6)
        for j0 in(0,joint):
            st[px(j0,s):px(j0+L,s),max(0,c-6):c+7]+=np.linspace(1,0,px(j0+L,s)-px(j0,s))[:,None]
    st=np.asarray(Image.fromarray((np.clip(st,0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)))/255
    lo=np.asarray(Image.fromarray(R.integers(0,256,(16,16)).astype(np.uint8)).resize((N,N),Image.BICUBIC))/255-0.5
    img=img*(1-0.035*st+0.008*lo)[...,None]+R.normal(0,1.5,(N,N,1))
    jc=np.array(rgb)*0.8
    for k in range(int(s/joint)+1):
        img[:,px(k*joint,s):px(k*joint,s)+2]=jc;img[px(k*joint,s):px(k*joint,s)+2,:]=jc
    Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(f'{d}/{nm}.png');print(nm,'sd %.1f'%img.mean(2).std())
render('white',(236,236,238));render('concrete',(196,190,178));render('path',(153,146,134),6,1.5)
