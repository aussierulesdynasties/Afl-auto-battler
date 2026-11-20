# Hand repaint of Norwood's flat walls (texture pass 2026-11-20). Runs after tex.py; no photo pixels.
# Panels with control joints, faint per-panel tone, soft vertical weathering streaks. Kept even (no mottle).
import numpy as np
from PIL import Image,ImageFilter
R=np.random.default_rng(11);PPM=128
def streaks(w,h):
    s=np.zeros((h,w));
    for _ in range(w//12):
        x=R.integers(0,w);L=R.integers(h//4,h);s[:L,x]+=R.uniform(0.4,1)*np.linspace(1,0,L)
    s=np.asarray(Image.fromarray((s*120).clip(0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))).astype(float)/120
    return np.tile(s,(1,1))
def panels(n,base,tw,th,pw,ph,jk,tsd,st=0.035):
    w,h=int(tw*PPM),int(th*PPM);x=np.arange(w)/PPM;y=np.arange(h)/PPM
    kx=(x//pw).astype(int);ky=(y//ph).astype(int)
    t=1+R.normal(0,tsd,(ky.max()+1,kx.max()+1))[ky[:,None],kx[None,:]]
    a=np.ones((h,w,3))*np.array(base,float)*t[...,None]
    a*=(1-st*streaks(w,h))[...,None]
    jx=(x%pw)<0.025;jy=(y%ph)<0.025;a[:,jx]*=jk;a[jy,:]*=jk
    a+=R.normal(0,1.5,(h,w,1))
    Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'../tex/{n}.png');print(n,(w,h),'sd %.1f'%a.mean(2).std())
panels('concrete',(168,166,160),3,3,1.5,1.0,0.84,0.018)
panels('concrete_dark',(132,130,126),2,2,1.0,1.0,0.84,0.018)
panels('render_cream',(214,204,180),2,2,1.0,2.0,0.88,0.012)
panels('render_white',(226,226,220),2,2,1.0,2.0,0.88,0.012)
panels('cladding_charcoal',(48,49,52),2,3,0.6,3.0,0.70,0.03,st=0.02)
panels('cladding_grey',(118,122,126),2,4,0.5,4.0,0.80,0.02,st=0.02)
import json
S=json.load(open('../tex/spec.json'));S['cladding_charcoal']['th']=3;S['cladding_grey']['th']=4;json.dump(S,open('../tex/spec.json','w'))
# perimeter fence: dark painted sheet panels (2 m), post every panel, faint seam lines, white capping kept
sp=S['fence_hoarding'];w,h=400,200;a=np.asarray(Image.open('../tex/fence_hoarding.png').convert('RGB')).astype(float).copy()
cap=16;x=np.arange(w)/w*sp['tw'];pan=(x//2.0).astype(int)
body=np.ones((h-cap,w,3))*np.array([36,38,38.])*(1+R.normal(0,0.03,pan.max()+1)[pan])[None,:,None]
body*=(1-0.05*streaks(w,h-cap))[...,None]
for k in range(int(sp['tw']/2)+1):
    c=int(k*2.0/sp['tw']*w);body[:,max(c-3,0):c+3]=[58,60,60];body[:,max(c-4,0):max(c-3,0)]=[22,23,23]
rb=(x%0.25);body[:,rb<0.03]*=1.22;body[:,(rb>=0.03)&(rb<0.05)]*=0.8
yy=np.arange(h-cap)/(h-cap);body[np.abs(yy-0.5)<0.006]*=1.35
a[cap:]=body+R.normal(0,1.5,(h-cap,w,1))
Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('../tex/fence_hoarding.png');print('fence sd %.1f'%a.mean(2).std())
