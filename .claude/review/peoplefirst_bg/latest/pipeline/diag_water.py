import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
s = np.asarray(Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400), Image.BOX)).astype(float)
t0 = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)
L=s.mean(2)
W1=ndimage.binary_closing(ndimage.binary_opening((L<55)&(s[...,2]>=s[...,0]-4)&(ndimage.median_filter(s[...,1]-s[...,2],5)<6),iterations=2),iterations=3)
W2=(t0[...,2]>t0[...,0]+25)&(t0[...,2]>t0[...,1]+5)
D=W1&~ndimage.binary_dilation(W2,iterations=3)
lab,n=ndimage.label(D); sz=ndimage.sum(D,lab,range(1,n+1)); o=np.argsort(-sz)
print('miss total',int(D.sum()),'comps',n)
sl=ndimage.find_objects(lab)
tiles=[]
for k in o[:12]:
    ys,xs=sl[k]; cy=(ys.start+ys.stop)//2; cx=(xs.start+xs.stop)//2; h=max(ys.stop-ys.start,xs.stop-xs.start)//2+20; h=max(h,60)
    y0,y1,x0,x1=max(cy-h,0),min(cy+h,1400),max(cx-h,0),min(cx+h,1400)
    a=Image.fromarray(s[y0:y1,x0:x1].astype(np.uint8)).resize((300,300)); b=Image.fromarray(t0[y0:y1,x0:x1].astype(np.uint8)).resize((300,300))
    m=Image.fromarray((D[y0:y1,x0:x1]*255).astype(np.uint8)).resize((300,300))
    t=Image.new('RGB',(900,320),'black'); t.paste(a,(0,20)); t.paste(m.convert('RGB'),(300,20)); t.paste(b,(600,20))
    ImageDraw.Draw(t).text((4,4),'#%d %d m2 world x %d y %d'%(len(tiles),sz[k],cx-700,700-cy),fill='yellow'); tiles.append(t)
    print(len(tiles)-1,int(sz[k]),cx-700,700-cy)
B=Image.new('RGB',(1800,320*6)); 
for i,t in enumerate(tiles): B.paste(t,((i%2)*900,(i//2)*320))
B.save('out/peoplefirst/water_miss.png')
