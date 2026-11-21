# hand-made podium opening textures (no photo pixels): 512 px = 4 m (uv = metres/4)
import numpy as np
from PIL import Image
rng=np.random.default_rng(7)
def save(a,n):Image.fromarray(np.clip(a,0,255).astype(np.uint8)).save('tex/'+n+'.png')
# pale warm-grey aluminium louvre: blade every 0.25 m, deeper shadow line every 0.5 m, mullion at each 4 m tile edge
a=np.zeros((512,512,3))+np.array([200,183,170]);y=np.arange(512)[:,None]
a-=((y%32)<3)[...,None]*np.array([38,36,34]);a-=((y%64)<5)[...,None]*np.array([30,28,26])
a[:,:8]=np.array([92,86,82]);a+=rng.normal(0,2.0,a.shape);save(a,'plouvre')
# grey tinted glass band with slim mullions every 1.6 m (205 px)
g=np.zeros((512,512,3))+np.array([132,127,124]);x=np.arange(512)[None,:]
g-=((x%205)<6)[...,None]*np.array([50,48,46]);g+=np.linspace(6,-6,512)[:,None,None];g+=rng.normal(0,1.5,g.shape);save(g,'pglass')
