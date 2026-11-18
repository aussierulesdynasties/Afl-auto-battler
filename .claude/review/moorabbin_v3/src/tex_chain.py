# hand-made chain-wire tile (procedural, no photo pixels): 0.5 m square, 60 mm diamonds, galvanised wire
import numpy as np,json
from PIL import Image
N=256;M=0.5;P=0.06
y,x=np.mgrid[0:N,0:N]*(M/N)
u=(x+y)/P;v=(x-y)/P
d=np.minimum(np.abs(u-np.round(u)),np.abs(v-np.round(v)))*P/np.sqrt(2)
wire=d<0.0022
img=np.zeros((N,N,4),np.uint8)
shade=(150+40*np.cos(u*np.pi*2)).astype(np.uint8)
img[...,0]=shade;img[...,1]=shade;img[...,2]=(shade*1.03).clip(0,255).astype(np.uint8);img[...,3]=np.where(wire,255,0)
Image.fromarray(img,'RGBA').save('hand/chainwire.png')
T=json.load(open('hand/tiles.json'));T['chainwire']=[M,M];json.dump(T,open('hand/tiles.json','w',newline=''))
print('wire px',wire.mean())
