exec(open('pj.py',encoding='utf-8').read())
import sys
from PIL import ImageDraw
ZR_IN,ZR_OUT,DR_IN,DR_OUT=8.9,15.6,19.7,35.2
def zroof(d):return ZR_IN+(ZR_OUT-ZR_IN)*(d-DR_IN)/(DR_OUT-DR_IN)
x0,y0,x1,y1,sc=map(int,sys.argv[1:6]);S=list(range(*map(int,sys.argv[6:9])));D=[float(v) for v in sys.argv[9].split(',')]
outs=[]
for src in('ref.jpg','out/render.png'):
    im=Image.open(src).convert('RGB').resize((1023,576),Image.LANCZOS).crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
    for s in S:
        for d in D:
            p=proj(P([s],d,zroof(d))[0])[0];X,Y=(p[0]-x0)*sc,(p[1]-y0)*sc
            dr.ellipse((X-3,Y-3,X+3,Y+3),outline='white');dr.text((X+4,Y-5),'%g'%d,fill='white')
        p=proj(P([s],D[-1],zroof(D[-1]))[0])[0];dr.text(((p[0]-x0)*sc-10,(p[1]-y0)*sc+8),'s%d'%s,fill='yellow')
    outs.append(im)
w,h=outs[0].size;b=Image.new('RGB',(w,h*2));b.paste(outs[0],(0,0));b.paste(outs[1],(0,h));b.save('out/samp2.png')
