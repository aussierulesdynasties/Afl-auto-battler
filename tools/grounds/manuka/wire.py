# draw model rings / edges for named objects (prefix match) on a photo crop: python wire.py out x0 y0 x1 y1 names...
import sys,json,numpy as np;from cam import proj;from PIL import Image,ImageDraw
D=json.load(open('model.json'));out=sys.argv[1];x0,y0,x1,y1=map(int,sys.argv[2:6]);names=sys.argv[6:]
k=min(1400/(x1-x0),3.0);im=Image.open('photo.png').convert('RGB').crop((x0,y0,x1,y1)).resize((int((x1-x0)*k),int((y1-y0)*k)),Image.LANCZOS);d=ImageDraw.Draw(im)
cols=[(255,0,255),(0,255,255),(255,255,0),(255,80,80),(80,255,80),(80,160,255),(255,160,0),(255,255,255)]
T=lambda p:((p[0]-x0)*k,(p[1]-y0)*k);ci=0
for o in D['objs']:
    if not any(o['name'].startswith(nm) for nm in names):continue
    V=np.array(o['v']);Y=proj(V)
    if o['n']:
        n=o['n']
        for j in range(n):
            c=cols[ci%8];ci+=1;L=[T(p) for p in Y[j::n]];d.line(L,fill=c,width=2)
            W,H=im.size;ins=[q for q in L if 0<q[0]<W-60 and 5<q[1]<H-5]
            for q in ins[::max(1,len(ins)//3)]:d.text((q[0],q[1]-11),f"{o['name'][2:]}{j}",fill=c)
    else:
        c=cols[ci%8];ci+=1
        for f in o['f']:d.line([T(Y[i]) for i in f+[f[0]]],fill=c,width=1)
for x in range((x0//50+1)*50,x1,50):d.text(((x-x0)*k,2),str(x),fill=(255,255,255))
for y in range((y0//50+1)*50,y1,50):d.text((2,(y-y0)*k),str(y),fill=(255,255,255))
im.save(out)
