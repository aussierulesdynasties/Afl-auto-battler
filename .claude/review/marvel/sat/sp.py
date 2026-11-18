# Stadium-frame true plan at height z: u along long axis (south+), v across (west+), origin = pitch centroid.
# python sp.py z u0 u1 v0 v1 res out   (res m/px; image x = (v1-v)/res, y = (u-u0)/res: north up, west left)
import sys,math,numpy as np
from PIL import Image,ImageDraw
A=np.asarray(Image.open('lplan_all_clean.png').convert('RGB'))
O=np.array([-7.12,-6.5]);import os;th=math.radians(float(os.environ.get('TH','-7.27')));U=np.array([math.cos(th),math.sin(th)]);V=np.array([-U[1],U[0]])
K=np.array([-6.94,-2.2])/38.0
z,u0,u1,v0,v1,r=map(float,sys.argv[1:7]);out=sys.argv[7]
uu=np.arange(u0,u1,r);vv=np.arange(v1,v0,-r);g_u,g_v=np.meshgrid(uu,vv,indexing='ij')
st=O+g_u[...,None]*U+g_v[...,None]*V+K*z
x=(200-st[...,1])*4;y=(st[...,0]+200)*4
x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=(x-x0)[...,None];fy=(y-y0)[...,None]
x0=np.clip(x0,0,1598);y0=np.clip(y0,0,1598)
o=A[y0,x0]*(1-fx)*(1-fy)+A[y0,x0+1]*fx*(1-fy)+A[y0+1,x0]*(1-fx)*fy+A[y0+1,x0+1]*fx*fy
im=Image.fromarray(o.astype(np.uint8));d=ImageDraw.Draw(im);step=float(sys.argv[8]) if len(sys.argv)>8 else 5
k=math.ceil(u0/step)*step
while k<u1:
    Y=(k-u0)/r;d.line([(0,Y),(im.width,Y)],fill=(255,230,0) if k%(step*2)==0 else (150,140,0));d.text((2,Y+1),'u%g'%k,fill=(255,40,255));k+=step
k=math.ceil(v0/step)*step
while k<v1:
    X=(v1-k)/r;d.line([(X,0),(X,im.height)],fill=(0,230,255) if k%(step*2)==0 else (0,130,150));d.text((X+2,12),'v%g'%k,fill=(255,40,255));k+=step
im.save(out,quality=90);print(im.size)
