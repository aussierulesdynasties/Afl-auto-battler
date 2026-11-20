# Hand repaint of ENGIE's flat surfaces (texture pass 2026-11-20). Runs after texgen.py; no photo pixels.
# Render walls (4 m tile): 1.33 m panels, control joints, faint per-panel tone. Paving (4 m tile): 1 m slabs, joints.
# Kept even (director: no blotchy mottle).
import numpy as np
from PIL import Image
R=np.random.default_rng(9);N=400
def save(n,a):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save(f'tex/{n}.png');print(n,'sd %.1f'%a.mean(2).std())
def panels(n,base,pw,ph,jk,tsd):
    x=np.arange(N)/N*4;kx=(x//pw).astype(int);ky=(x//ph).astype(int)
    t=1+R.normal(0,tsd,(ky.max()+1,kx.max()+1))[ky[:,None],kx[None,:]]
    a=np.ones((N,N,3))*base*t[...,None]
    jx=(x%pw)<0.03;jy=(x%ph)<0.03;a[:,jx]*=jk;a[jy,:]*=jk
    save(n,a+R.normal(0,1.5,(N,N,1)))
panels('red_render',(150,58,51),1.333,2.0,0.82,0.015);panels('white_render',(232,232,227),1.333,2.0,0.86,0.012)
panels('concrete',(178,176,170),1.0,1.0,0.86,0.02);panels('deck',(150,148,144),1.0,1.0,0.86,0.02)
