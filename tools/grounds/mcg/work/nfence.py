import sys,json,numpy as np;sys.path.insert(0,'work');import tri,earthcam as E
from PIL import Image,ImageDraw
from PIL import ImageOps,ImageEnhance
im0=Image.open('ge/n_c.png').convert('RGB');im0=ImageEnhance.Brightness(ImageOps.autocontrast(im0,cutoff=2)).enhance(1.8);im=np.asarray(im0).astype(float)
c=tri.camv('n_c');cu,cv=E.proj(c,[0,0,-5.3])
r,g,b=im[...,0],im[...,1],im[...,2];green=(g>r+15)&(g>b+25)&(g>60)
out=[];pts=[]
for bdeg in range(0,360,3):
    a=np.radians(bdeg);dx,dy=np.sin(a),-np.cos(a) # bearing: 0=north=up
    last=None
    for s in np.arange(150,420,0.5):
        u,v=int(cu+dx*s),int(cv+dy*s)
        # majority green in 5x5
        if green[v-2:v+3,u-2:u+3].mean()>0.5: last=s
        elif last is not None and s-last>12: break
    u,v=cu+dx*last,cv+dy*last;X=tri.onz('n_c',u,v,-5.3)
    out.append([bdeg,round(float(np.hypot(X[0],X[1])),1),round(float(X[0]),1),round(float(X[1]),1)]);pts.append((u,v))
json.dump(out,open('work/fence_n.json','w'))
I=im0.copy();d=ImageDraw.Draw(I);d.line(pts+[pts[0]],fill=(255,0,255),width=2)
I.crop((700,300,1250,800)).save('work/fence_n.png')
for o in out[::6]:print(o)
