# photo with the render's edges drawn on it (magenta), cropped regions at zoom
import sys,numpy as np;from PIL import Image
rd=np.array(Image.open(sys.argv[1]).convert('RGBA')).astype(int);ph=np.array(Image.open('photo.png').convert('RGB'))
c=rd[...,:3]+rd[...,3:4]*3
e=np.zeros(c.shape[:2],bool)
dx=np.abs(np.diff(c,axis=1)).sum(2)>40;dy=np.abs(np.diff(c,axis=0)).sum(2)>40
e[:,1:]|=dx;e[1:,:]|=dy
o=ph.copy();o[e]=(255,0,255)
im=Image.fromarray(o);im.save(sys.argv[2])
reg={'w':(100,330,800,1100),'n':(650,300,1700,700),'s':(450,850,1550,1120),'e':(1350,350,1920,1000)}
for k,(x0,y0,x1,y1) in reg.items():
    k2=min(1400/(x1-x0),2.0);im.crop((x0,y0,x1,y1)).resize((int((x1-x0)*k2),int((y1-y0)*k2)),Image.LANCZOS).save(sys.argv[2].replace('.png',f'_{k}.png'))
