# polar unwrap of the satellite (lean corrected z 20): x = angle (6 px/deg), y = d past the pitch line (6 px/m, outward = up)
# red = model outer edge (top render mask); ticks every 1 m (yellow) / 5 m (cyan, labelled); angle labels every 5 deg
import sys,math,numpy as np;sys.path.insert(0,'.')
from zk import rp,PCx,PCy
from PIL import Image,ImageDraw
from scipy import ndimage
CX,CY,H,M=-10.75,-24.16,220.0,0.25
a0,a1,d0,d1,out=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
PA,PD=6,6
s=np.asarray(Image.open('sat19_local.png').convert('RGB')).astype(float);m=np.load('mask.npy').astype(float)
A=np.arange(a0,a1,1/PA);D=np.arange(d1,d0,-1/PD)
AA,DD=np.meshgrid(A,D);T=np.radians(AA);R=np.vectorize(rp)(AA)+DD
X=PCx+R*np.cos(T);Y=PCy+R*np.sin(T)
U=(X-CX+H)/M;V=(CY+H-(Y+0.035*20))/M;Vm=(CY+H-Y)/M
img=np.stack([ndimage.map_coordinates(s[...,c],[V,U],order=1) for c in range(3)],-1).astype(np.uint8)
mk=ndimage.map_coordinates(m,[Vm,U],order=0)>0.5
im=Image.fromarray(img);d=ImageDraw.Draw(im)
for j in range(len(A)):
    col=mk[:,j];idx=np.where(col)[0]
    if len(idx):i=idx.min();d.point([(j,i),(j,i+1)],fill=(255,0,0))
for k in range(int(math.ceil(d0)),int(d1)+1):
    y=(d1-k)*PD;c=(0,255,255) if k%5==0 else (255,255,0);d.line([(0,y),(6 if k%5 else 12,y)],fill=c)
    if k%5==0:d.text((14,y-5),str(k),fill=c)
for a in range(int(math.ceil(a0)),int(a1)+1):
    x=(a-a0)*PA
    if a%5==0:d.line([(x,0),(x,10)],fill=(0,255,255));d.text((x+2,12),str(a),fill=(0,255,255))
im.save(out)
