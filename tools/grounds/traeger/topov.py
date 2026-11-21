# python topov.py MODEL.png SAT.png prims.json OUT x0 y0 x1 y1 ppm : top-down model over the satellite, model fence lines drawn, then turned north-up
import json,sys,math,numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
M=Image.open(sys.argv[1]).convert('RGBA');S=Image.open(sys.argv[2]).convert('RGBA');P=json.load(open(sys.argv[3]));out=sys.argv[4]
x0,y0,x1,y1,k=map(float,sys.argv[5:10]);assert M.size==S.size,(M.size,S.size)
px=lambda p:((p[0]-x0)*k,(y1-p[1])*k)
a=np.asarray(M)[:,:,3]>40
edge=Image.fromarray((a.astype(np.uint8)*255)).filter(ImageFilter.FIND_EDGES)
def comp(alpha):
    m=np.asarray(M).astype(float);s=np.asarray(S).astype(float);o=s.copy();w=(m[:,:,3:4]/255)*alpha
    o[:,:,:3]=s[:,:,:3]*(1-w)+m[:,:,:3]*w;im=Image.fromarray(o.astype(np.uint8));d=ImageDraw.Draw(im)
    e=np.asarray(edge)>0;arr=np.asarray(im).copy();arr[e]=(255,0,255,255);im=Image.fromarray(arr);d=ImageDraw.Draw(im)
    for p in P:
        if 'pts' in p and p['kind']=='fence':
            pts=[px(q) for q in p['pts']]
            if not p.get('open'):pts.append(pts[0])
            d.line(pts,fill=(0,255,255,255),width=2)
    return im
for tag,al in (('half',0.5),('lines',0.0)):
    im=comp(al);th=json.load(open('align.json'))['s'][0]
    im=im.rotate(math.degrees(th),expand=True,resample=Image.BICUBIC,fillcolor=(20,20,20,255))
    d=ImageDraw.Draw(im);W,H=im.size
    d.polygon([(W-60,30),(W-72,70),(W-48,70)],fill=(255,255,255));d.text((W-65,74),'N',fill=(255,255,255))
    d.rectangle([20,H-40,20+50*k,H-34],fill=(255,255,255));d.text((20,H-30),'50 m',fill=(255,255,255))
    im.convert('RGB').save(out.replace('.png','_%s.png'%tag))
print('OV OK',M.size)
