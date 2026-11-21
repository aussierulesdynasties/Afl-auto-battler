import sys,glob,os
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
fs=sorted(glob.glob('tex/*.png'))+glob.glob('data/gmhba/prep/ground_baked.png')+glob.glob('out/gmhba/ground_baked.png')
for f in fs:
    a=np.asarray(Image.open(f).convert('L').reduce(4) if os.path.getsize(f)>2e7 else Image.open(f).convert('L'),dtype=np.float32)
    print('%-45s %6.1f %s'%(f,a.std(),'LOW' if a.std()<10 else ''))
