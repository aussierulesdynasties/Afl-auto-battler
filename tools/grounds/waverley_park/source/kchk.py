exec(open('pj.py',encoding='utf-8').read())
import sys
from PIL import ImageDraw
x0,y0,x1,y1,sc=map(int,sys.argv[1:6]);pts=eval(sys.argv[6]);out=sys.argv[7]   # (s,d,zabs,label)
outs=[]
for src in('ref.jpg','out/render.png'):
    im=Image.open(src).convert('RGB').resize((1023,576),Image.LANCZOS).crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
    for s,d,z,lb in pts:
        p=proj(P([s],d,z)[0])[0];X,Y=(p[0]-x0)*sc,(p[1]-y0)*sc
        dr.ellipse((X-2,Y-2,X+2,Y+2),outline='cyan');dr.text((X+3,Y-5),lb,fill='cyan')
    outs.append(im)
w,h=outs[0].size;b=Image.new('RGB',(w,h*2));b.paste(outs[0],(0,0));b.paste(outs[1],(0,h));b.save(out)
