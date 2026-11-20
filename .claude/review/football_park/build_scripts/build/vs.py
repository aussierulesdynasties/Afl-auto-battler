# photo | render (matched camera) | 50% overlay, same size, labelled
import sys
from PIL import Image,ImageDraw,ImageFont
ph,rd,out,H=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4])
p=Image.open(ph).convert('RGB');r=Image.open(rd).convert('RGBA').resize(p.size,Image.LANCZOS)
bg=Image.new('RGBA',p.size,(58,62,66,255));bg.alpha_composite(r);rr=bg.convert('RGB')
ov=Image.blend(p,Image.composite(rr,p,r.split()[3]),0.5)
s=H/p.size[1];W=int(p.size[0]*s)
o=Image.new('RGB',(W*3+20,H+34),(24,24,24));d=ImageDraw.Draw(o)
try:f=ImageFont.truetype('arial.ttf',22)
except: f=None
for i,(im,lab) in enumerate([(p,'Photo'),(rr,'Model, from the photo camera'),(ov,'Overlay 50/50')]):
    o.paste(im.resize((W,H),Image.LANCZOS),(i*(W+10),34));d.text((i*(W+10)+6,6),lab,fill=(240,240,240),font=f)
o.save(out);print(o.size)
