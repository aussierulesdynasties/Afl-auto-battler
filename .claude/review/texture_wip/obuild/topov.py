# Top-down gate overlay: satellite (Esri z19, 0.25 m/px, north up) + model silhouette (cyan) + model edges (magenta) + 10 m grid
import sys,numpy as np
from PIL import Image,ImageDraw,ImageFilter
X0,Y1,R=-260,230,0.25
sat=Image.open('sat/sat_025.png').convert('RGB');top=Image.open(sys.argv[1]).convert('RGBA');out=sys.argv[2]
a=np.asarray(top.split()[3])>8
lum=np.asarray(top.convert('L')).astype(float)
gx=np.abs(np.diff(lum,axis=1,prepend=lum[:,:1]));gy=np.abs(np.diff(lum,axis=0,prepend=lum[:1]))
ed=((gx+gy)>40)&a
am=Image.fromarray((a*255).astype(np.uint8));ae=np.asarray(am.filter(ImageFilter.FIND_EDGES))>0
ed=ed|ae
S=np.asarray(sat).astype(float)
o=S.copy();o[a]=o[a]*0.6+np.array([0,255,255])*0.4
o[ed]=[255,0,255]
im=Image.fromarray(o.astype(np.uint8));d=ImageDraw.Draw(im)
W,H=im.size
for x in range(-260,241,10):
    px=(x-X0)/R;d.line([(px,0),(px,H)],fill=(255,255,0) if x%50 else (255,140,0),width=1)
for y in range(-230,231,10):
    py=(Y1-y)/R;d.line([(0,py),(W,py)],fill=(255,255,0) if y%50 else (255,140,0),width=1)
for x in range(-250,241,50):d.text(((x-X0)/R+3,3),str(x),fill=(255,255,255))
for y in range(-200,231,50):d.text((3,(Y1-y)/R+3),str(y),fill=(255,255,255))
im.save(out)
if len(sys.argv)>3:
    for spec in sys.argv[3:]:
        n,x0,x1,y0,y1,s=spec.split(',');x0,x1,y0,y1,s=float(x0),float(x1),float(y0),float(y1),int(s)
        c=im.crop((int((x0-X0)/R),int((Y1-y1)/R),int((x1-X0)/R),int((Y1-y0)/R)));c=c.resize((c.size[0]*s,c.size[1]*s),Image.NEAREST)
        sc=Image.fromarray(S.astype(np.uint8)).crop((int((x0-X0)/R),int((Y1-y1)/R),int((x1-X0)/R),int((Y1-y0)/R))).resize(c.size,Image.LANCZOS)
        b=Image.new('RGB',(c.size[0]*2+8,c.size[1]),'black');b.paste(sc,(0,0));b.paste(c,(c.size[0]+8,0));b.save(out.replace('.png','_%s.png'%n))
