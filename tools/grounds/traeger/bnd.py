import numpy as np,math,json
from PIL import Image,ImageDraw
from cam import *
p=load();im=np.asarray(Image.open('refs/ref.jpg').convert('RGB')).astype(float)
out=[]
for th in np.radians(np.arange(0,360,3)):
    best=None
    for r in np.arange(55,100,0.15):
        X=(r*math.cos(th),r*math.sin(th),0);u,v=proj(p,X)[0]
        if not(2<u<1497 and 2<v<1071):continue
        c=im[int(v),int(u)];w=c.min()-0.5*(c.max()-c.min())  # white: bright and grey
        if best is None or w>best[0]:best=(w,r,u,v)
    if best and best[0]>120:out.append((math.degrees(th),best[1],best[2],best[3],best[0]))
dbg=Image.open('refs/ref.jpg').convert('RGB');d=ImageDraw.Draw(dbg)
for a,r,u,v,w in out:d.ellipse([u-3,v-3,u+3,v+3],outline=(255,0,255))
dbg.save('bnd_dbg.png');json.dump(out,open('bnd.json','w'))
for o in out:print([round(x,1) for x in o])
