import sys, numpy as np
src=open('meas_table.py',encoding='utf-8').read()
cut=src.index("spec = json.load")
cut2=src.index("rows.append(('Water area")
exec(src[:cut]); exec(src[cut:cut2])
from PIL import Image, ImageDraw
from scipy import ndimage
for name,D in (('miss',W1&~ndimage.binary_dilation(W2,iterations=2)),('extra',W2&~ndimage.binary_dilation(W1,iterations=2))):
    lab,n=ndimage.label(D); sz=ndimage.sum(D,lab,range(1,n+1)); o=np.argsort(-sz); sl=ndimage.find_objects(lab)
    print(name,'total',int(D.sum()))
    tiles=[]
    for k in o[:12]:
        ys,xs=sl[k]; cy=(ys.start+ys.stop)//2; cx=(xs.start+xs.stop)//2; h=max(max(ys.stop-ys.start,xs.stop-xs.start)//2+20,60)
        y0,y1,x0,x1=max(cy-h,0),min(cy+h,1400),max(cx-h,0),min(cx+h,1400)
        f=lambda a:Image.fromarray(a[y0:y1,x0:x1].astype(np.uint8)).resize((300,300))
        t=Image.new('RGB',(900,320)); t.paste(f(s),(0,20)); t.paste(f(D*255.).convert('RGB'),(300,20)); t.paste(f(t0),(600,20))
        ImageDraw.Draw(t).text((4,4),'#%d %d m2 x %d y %d'%(len(tiles),sz[k],cx-700,700-cy),fill='yellow'); tiles.append(t); print(len(tiles)-1,int(sz[k]),cx-700,700-cy)
    B=Image.new('RGB',(1800,320*6))
    for i,t in enumerate(tiles): B.paste(t,((i%2)*900,(i//2)*320))
    B.save('out/peoplefirst/water_%s.png'%name)
