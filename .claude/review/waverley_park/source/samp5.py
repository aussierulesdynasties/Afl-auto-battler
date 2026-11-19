exec(open('pj.py',encoding='utf-8').read())
import sys
from PIL import ImageDraw
ZGK=np.array([(0,0),(95,0),(110,4.5),(128,4.5),(140,4.5),(160,7),(175,11),(197,11),(201,11.5),(214,8.8),(220,8.33),(225,8.5),(235,9),(245,6),(320,5),(380,10),(400,10),(415,0),(PER,0)],float)
def ZG(s):return 10.0 if 136<=s<170 and KZ else float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]))
KZ=False
x0,y0,x1,y1,sc=map(int,sys.argv[1:6]);pts=eval(sys.argv[6])   # list of (s,d,dz,label)
outs=[]
for src in('ref.jpg','out/render.png'):
    im=Image.open(src).convert('RGB').resize((1023,576),Image.LANCZOS).crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
    for s,d,dz,lb in pts:
        p=proj(P([s],d,ZG(s)+dz)[0])[0];X,Y=(p[0]-x0)*sc,(p[1]-y0)*sc
        dr.ellipse((X-2,Y-2,X+2,Y+2),outline='cyan');dr.text((X+3,Y-5),lb,fill='cyan')
    outs.append(im)
w,h=outs[0].size;b=Image.new('RGB',(w,h*2));b.paste(outs[0],(0,0));b.paste(outs[1],(0,h));b.save('out/samp5.png')
