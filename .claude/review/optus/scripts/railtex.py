# hand-made textures for the terrace lamp posts, podium balustrade and plaza railing (no photo pixels); leaves info.json alone
import numpy as np,os
from PIL import Image
T=os.path.join(os.path.dirname(os.path.abspath(__file__)),'tex');rng=np.random.default_rng(7)
def save(n,a,mode='RGB'):Image.fromarray(np.clip(a,0,255).astype(np.uint8),mode).save(os.path.join(T,n+'.png'))
# dark powder-coated steel (o2: near-black railing on the plaza)
a=np.ones((64,64,3))*np.array([46,48,50],float)+rng.normal(0,2.5,(64,64,1));save('rail',a)
# lamp posts: mid-grey galvanised steel
a=np.ones((64,64,3))*np.array([128,130,131],float)+rng.normal(0,3,(64,64,1));a[:,::16]-=10;save('lamp',a)
# balustrade infill: light grey wire mesh, 1 m tile, wires every 6.25 cm, see-through between
S=128;a=np.zeros((S,S,4));a[...,:3]=(196,198,196);a[...,3]=70
for k in range(0,S,8):a[k:k+1,:,3]=200;a[:,k:k+1,3]=200
save('mesh',a,'RGBA')
print('railtex ok')
