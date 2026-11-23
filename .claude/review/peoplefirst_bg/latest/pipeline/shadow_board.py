import numpy as np
src=open('meas_table.py',encoding='utf-8').read(); exec(src[:src.index("rows.append(('Water area")])
from PIL import Image, ImageDraw
g=np.asarray(Image.open('data/peoplefirst/sat2.png').convert('RGB'))
tiles=[]
for d in _drop:
    ys,xs=np.nonzero(_lb==d); cy,cx=int(ys.mean()),int(xs.mean()); y0,x0=max(cy-40,0),max(cx-40,0)
    m=(_lb[y0:y0+80,x0:x0+80]==d)
    a=s[y0:y0+80,x0:x0+80].copy(); e=m&~ndimage.binary_erosion(m); a[e]=[255,0,0]
    t=Image.new('RGB',(330,180)); t.paste(Image.fromarray(a.astype(np.uint8)).resize((160,160)),(0,18)); t.paste(Image.fromarray(g[y0:y0+80,x0:x0+80]).resize((160,160)),(165,18))
    ImageDraw.Draw(t).text((2,2),'%d m2 x%d y%d'%(len(ys),cx-700,700-cy),fill='yellow'); tiles.append(t)
n=len(tiles); cols=6; B=Image.new('RGB',(cols*330,((n+cols-1)//cols)*180))
for i,t in enumerate(tiles): B.paste(t,((i%cols)*330,(i//cols)*180))
B.save('out/peoplefirst/water_shadow.png'); print(n,'dropped, total',int(sum(ndimage.sum(np.ones_like(_lb),_lb,_drop))))
