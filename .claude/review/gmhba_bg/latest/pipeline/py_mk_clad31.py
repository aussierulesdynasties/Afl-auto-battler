# trapezoidal wall cladding (Trimdek-style): 12 m tile, 1536 px (128 px/m); rib pitch 190 mm = 24 px -> 64 ribs, exact repeat.
# Each rib: 4 px lit flank, 4 px crest, 4 px shaded flank; pan flat between. Sheet = 4 ribs (762 mm): +-2.5% tone per sheet.
# Weathering: soft vertical streaks below 3% so the wall reads as one even metal surface, not curtains.
import numpy as np; from PIL import Image
N=1536; x=np.arange(N); p=x%24
row=np.full(N,0.80)
row[(p>=0)&(p<4)]=0.92; row[(p>=4)&(p<8)]=0.86; row[(p>=8)&(p<12)]=0.66
rng=np.random.default_rng(31); sheet=1+rng.uniform(-0.025,0.025,N//96+1); row*=sheet[x//96]
img=np.tile(row,(N,1))
y=np.arange(N)[:,None]/N; img*=1+0.02*np.sin(2*np.pi*(y*3+np.sin(2*np.pi*x/N*5)*0.2))
img*=1+rng.normal(0,0.008,(N,N))
img=np.clip(img,0,1); Image.fromarray((img*255).astype(np.uint8)).convert('RGB').save('tex/mt/clad_rib.png')
open('tex/mt/clad_rib.mean','w').write('%.4f'%img.mean()); print('mean',img.mean())
