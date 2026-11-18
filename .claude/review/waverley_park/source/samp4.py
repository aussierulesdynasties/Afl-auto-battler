exec(open('pj.py',encoding='utf-8').read())
import sys
from PIL import ImageDraw
ZGK=np.array([(0,0),(95,0),(110,4.5),(128,4.5),(140,4.5),(160,7),(175,11),(200,11),(212,8),(225,8.5),(235,9),(245,6),(320,5),(380,10),(400,10),(415,0),(PER,0)],float)
def ZG(s):return float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]))
x0,y0,x1,y1,sc=map(int,sys.argv[1:6]);S=list(range(*map(int,sys.argv[6:9])));DZ=[float(v) for v in sys.argv[9].split(',')];DD=float(sys.argv[10])
outs=[]
for src in('ref.jpg','out/render.png'):
    im=Image.open(src).convert('RGB').resize((1023,576),Image.LANCZOS).crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
    for s in S:
        for dz in DZ:
            p=proj(P([s],DD,ZG(s)+dz)[0])[0];X,Y=(p[0]-x0)*sc,(p[1]-y0)*sc
            dr.ellipse((X-3,Y-3,X+3,Y+3),outline='cyan');dr.text((X+4,Y-5),'%+g'%dz,fill='cyan')
        p=proj(P([s],DD,ZG(s))[0])[0];dr.text(((p[0]-x0)*sc-10,(p[1]-y0)*sc+10),'s%d'%s,fill='yellow')
    outs.append(im)
w,h=outs[0].size;b=Image.new('RGB',(w,h*2));b.paste(outs[0],(0,0));b.paste(outs[1],(0,h));b.save('out/samp4.png')
