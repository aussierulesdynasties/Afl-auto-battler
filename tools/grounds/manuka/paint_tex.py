# Hand repaint of Manuka's flat surfaces (texture pass 2026-11-20). Runs after tex.py; no photo pixels.
# Roofs: profiled sheet ribs every 0.8 m plus a lap joint every 4 m. Walls: 1.2 m panels, joints, faint per-panel tone.
# Kept even (director: no blotchy mottle).
import numpy as np, json
from PIL import Image
R=np.random.default_rng(5);T=json.load(open('tex/tiles.json'))
def save(n,a):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{n}.png');print(n,'sd %.1f'%a.mean(2).std())
def roof(n,base):
    mu,mv=T[n];N=512;x=np.arange(N)/N*mu
    ph=(x%0.8)/0.8;prof=np.where(ph<0.12,1.10,np.where(ph<0.2,0.86,1.0))   # lit rib face, shaded flank, pan
    a=np.ones((N,N,3))*base*prof[None,:,None]
    a[:2,:]*=0.85                                                            # lap joint at the tile edge (4 m)
    save(n,a+R.normal(0,1.2,(N,N,1)))
def wall(n,base,pw=1.2,jk=0.82):
    mu,mv=T[n];H,W=Image.open(f'tex/{n}.png').size[::-1];x=np.arange(W)/W*mu
    a=np.ones((H,W,3))*base
    k=(x//pw).astype(int);tone=1+R.normal(0,0.012,k.max()+1)[k];a*=tone[None,:,None]
    a[:,(x%pw)<0.025]*=jk;a[:3,:]*=jk;save(n,a+R.normal(0,1.2,(H,W,1)))
roof('roof_white',(236,237,239));roof('roof_grey',(150,155,160));roof('roof_pav',(120,132,150))
wall('white',(238,238,236));wall('dark',(58,60,66),pw=1.5,jk=0.7)
