# python board.py PHOTO RENDER OUT x0 y0 x1 y1 scale [title]
import sys,numpy as np
from PIL import Image,ImageDraw,ImageFilter
ph=Image.open(sys.argv[1]).convert('RGB');rd=Image.open(sys.argv[2]).convert('RGBA')
x0,y0,x1,y1=[int(v) for v in sys.argv[4:8]];sc=float(sys.argv[8])
ph=ph.crop((x0,y0,x1,y1));rd=rd.crop((x0,y0,x1,y1))
W,H=int((x1-x0)*sc),int((y1-y0)*sc);ph=ph.resize((W,H),Image.LANCZOS);rd=rd.resize((W,H),Image.LANCZOS)
bg=Image.new('RGB',(W,H),(40,40,40));rdo=bg.copy();rdo.paste(rd,(0,0),rd)
ov=ph.copy();ov=Image.blend(ov,rdo,0.5)
# edge lines of render on photo
a=np.asarray(rd.convert('L').filter(ImageFilter.FIND_EDGES)).astype(float)
e=Image.fromarray((a>40).astype(np.uint8)*255);ov2=ph.copy();ov2.paste(Image.new('RGB',(W,H),(255,0,255)),(0,0),e)
out=Image.new('RGB',(W*2,H*2),(20,20,20))
out.paste(ph,(0,0));out.paste(rdo,(W,0));out.paste(ov,(0,H));out.paste(ov2,(W,H))
d=ImageDraw.Draw(out)
for i,t in enumerate(['photo','render (photo camera)','50% overlay','render edges on photo']):d.text(((i%2)*W+8,(i//2)*H+6),t,fill=(255,255,0))
out.save(sys.argv[3])
