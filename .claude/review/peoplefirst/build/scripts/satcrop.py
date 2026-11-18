import json,sys
from PIL import Image,ImageDraw
S=json.load(open('sat.json'));m=S['mpp']
x0,y0,x1,y1,step,k=map(float,sys.argv[2:8])
P=lambda x,y:(S['px']+x/m,S['py']-y/m)
im=Image.open('sat.png').convert('RGB')
a,b=P(x0,y1);c,e=P(x1,y0);im=im.crop((int(a),int(b),int(c),int(e)));im=im.resize((int(im.width*k),int(im.height*k)));d=ImageDraw.Draw(im)
Q=lambda x,y:((S['px']+x/m-int(a))*k,(S['py']-y/m-int(b))*k)
v=int(x0//step*step)
while v<=x1:
    d.line([Q(v,y0),Q(v,y1)],fill=(255,0,0) if v%50==0 else (255,140,140));d.text(Q(v,y1),str(v),fill=(255,255,0));v+=int(step)
v=int(y0//step*step)
while v<=y1:
    d.line([Q(x0,v),Q(x1,v)],fill=(255,0,0) if v%50==0 else (255,140,140));d.text(Q(x0,v),str(v),fill=(0,255,255));v+=int(step)
im.save(sys.argv[1])
