# Hand repaint of Albury's flat walls (texture pass 2026-11-20). Run after model/paint.py; no photo pixels.
# Render: 1 m x 2 m panels with control joints, faint per-panel tone, soft weathering streaks. Courts: acrylic grain.
import numpy as np
from PIL import Image,ImageFilter
R=np.random.default_rng(12);N=1024;T=2.0;PPM=N/T
def streaks():
    s=np.zeros((N,N))
    for _ in range(N//14):
        x=R.integers(0,N);L=R.integers(N//4,N);s[:L,x]+=R.uniform(0.4,1)*np.linspace(1,0,L)
    return np.asarray(Image.fromarray((s*120).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(float)/120
def panels(n,base,pw,ph,jk,tsd,st=0.035):
    x=np.arange(N)/PPM;kx=(x//pw).astype(int);ky=(x//ph).astype(int)
    t=1+R.normal(0,tsd,(ky.max()+1,kx.max()+1))[ky[:,None],kx[None,:]]
    a=np.ones((N,N,3))*np.array(base,float)*t[...,None]*(1-st*streaks())[...,None]
    j=(x%pw)<0.012;a[:,j]*=jk;j=(x%ph)<0.012;a[j,:]*=jk
    a+=R.normal(0,1.5,(N,N,1));Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('model/tex/'+n+'.png');print(n,'sd %.1f'%a.mean(2).std())
panels('render_cream',(226,214,184),1.0,2.0,0.88,0.012)
panels('paint_white',(236,236,232),1.0,2.0,0.90,0.010,st=0.03)
panels('render_grey',(186,184,178),1.0,2.0,0.86,0.014)
panels('render_pale',(240,235,220),1.0,2.0,0.88,0.010)
for n,c in (('court_green',(70,128,98)),('court_red',(176,62,52))):
    g=R.normal(0,1,(N,N));g=np.asarray(Image.fromarray(((g*30)+128).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(float)-128
    a=np.ones((N,N,3))*np.array(c,float)*(1+g[...,None]/128*0.5);Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('model/tex/'+n+'.png');print(n,'sd %.1f'%a.mean(2).std())
# Blank club boards (no lettering, director 2026-11-18): painted metal sheets, faint seams, soft fade and grime at the base.
def board(n,bg,border=None,sheets=4):
    im=Image.open('model/tex/'+n+'.png').convert('RGB');W,H=im.size
    a=np.ones((H,W,3))*np.array(bg,float)
    lo=np.asarray(Image.fromarray((R.normal(128,40,(H//32+1,W//32+1))).clip(0,255).astype(np.uint8)).resize((W,H),Image.BICUBIC)).astype(float)-128
    a*=(1+lo[...,None]/128*0.02)
    a*=(1-0.10*(np.linspace(0,1,H)**3))[:,None,None]
    for k in range(1,sheets):a[:,int(W*k/sheets)-1:int(W*k/sheets)+2]*=0.86
    a+=R.normal(0,2,(H,W,1));a=np.clip(a,0,255).astype(np.uint8);im=Image.fromarray(a)
    if border:
        from PIL import ImageDraw;ImageDraw.Draw(im).rectangle([4,4,W-5,H-5],outline=border,width=8)
    im.save('model/tex/'+n+'.png');print(n,'sd %.1f'%np.asarray(im).mean(2).std())
board('sign_tigers_club',(250,212,30),(20,20,20),3)
board('sign_tigers_ltd',(168,72,48),None,6)
board('sign_tradition',(22,22,24),None,8)
