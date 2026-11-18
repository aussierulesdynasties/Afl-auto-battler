import json,sys
from PIL import Image,ImageDraw
S=json.load(open('sat.json'));G=json.load(open('osm/geo.json'))
im=Image.open('sat.png').convert('RGB');d=ImageDraw.Draw(im)
m=S['mpp'];P=lambda x,y:(S['px']+x/m,S['py']-y/m)
step=int(sys.argv[2]) if len(sys.argv)>2 else 25
for v in range(-275,276,step):
    c=(255,0,0) if v%50==0 else (255,150,150)
    d.line([P(v,-300),P(v,300)],fill=c);d.line([P(-300,v),P(300,v)],fill=c)
    if v%50==0:
        for w in range(-250,251,100):d.text(P(v,w),str(v),fill=(255,255,0));d.text(P(w,v),str(v),fill=(0,255,255))
if 'osm' in sys.argv[1]:
    for k,pts in G.items():d.line([P(*p) for p in pts],fill=(0,255,0),width=2)
r=float(sys.argv[3]) if len(sys.argv)>3 else 170
a,b=P(-r,r);c_,e=P(r,-r);im=im.crop((int(a),int(b),int(c_),int(e)))
im.save(sys.argv[1])
