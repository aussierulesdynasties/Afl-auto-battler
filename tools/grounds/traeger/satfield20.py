# satellite resampled into the field frame. python satfield.py X0 X1 Y0 Y1 px_per_m gridstep out
import sys,json,numpy as np
from PIL import Image,ImageDraw
X0,X1,Y0,Y1,ppm,gs=map(float,sys.argv[1:7]);out=sys.argv[7]
im=np.asarray(Image.open('sat/gs20.png').convert('RGB')).astype(float);J=json.load(open('sat/gs20.png.json'))
W=int((X1-X0)*ppm);H=int((Y1-Y0)*ppm)
xs=X0+(np.arange(W)+.5)/ppm;ys=Y1-(np.arange(H)+.5)/ppm;XX,YY=np.meshgrid(xs,ys)
px=XX*0.911+YY*0.413;py=-XX*0.413+YY*0.911
u=(J['cx']-J['tx0'])*256+px/J['mpp']-.5;v=(J['cy']-J['ty0'])*256-py/J['mpp']-.5
u0=np.floor(u).astype(int);v0=np.floor(v).astype(int);fu=(u-u0)[...,None];fv=(v-v0)[...,None]
g=lambda a,b:im[np.clip(b,0,im.shape[0]-1),np.clip(a,0,im.shape[1]-1)]
o=(g(u0,v0)*(1-fu)*(1-fv)+g(u0+1,v0)*fu*(1-fv)+g(u0,v0+1)*(1-fu)*fv+g(u0+1,v0+1)*fu*fv)
I=Image.fromarray(o.clip(0,255).astype(np.uint8));d=ImageDraw.Draw(I)
for x in np.arange(np.ceil(X0/gs)*gs,X1,gs):
    X=(x-X0)*ppm;d.line([(X,0),(X,H)],fill=(255,0,0) if x%(gs*5)==0 else (255,140,140));d.text((X+2,2),'%g'%x,fill=(255,255,0))
for y in np.arange(np.ceil(Y0/gs)*gs,Y1,gs):
    Y=(Y1-y)*ppm;d.line([(0,Y),(W,Y)],fill=(255,0,0) if y%(gs*5)==0 else (255,140,140));d.text((2,Y+2),'%g'%y,fill=(255,255,0))
I.save(out)
