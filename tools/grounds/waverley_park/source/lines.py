exec(open('pj.py').read())
import sys
from PIL import ImageDraw
SEG=json.load(open('segs.json'))
def zb(d):
    if d<=19.2:return 1.0+0.28*d/0.8
    if d<=21.6:return 7.72
    return 7.72+0.28*(d-21.6)/0.8+0.3
nm,x0,y0,x1,y1,sc=sys.argv[1],*map(int,sys.argv[2:7])
im=Image.open('ref.jpg').convert('RGB').crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
def T(p):return [((q[0]-x0)*sc,(q[1]-y0)*sc) for q in p]
ss=np.arange(0,PER,0.5)
for d,c in((19.2,(0,255,255)),(21.6,(0,255,0)),(25,(255,255,0)),(28,(255,128,0)),(31,(255,0,255)),(34.4,(255,0,0))):
    dr.line(T(proj(np.c_[P(ss,d,0)[:,:2],np.full(len(ss),zb(d))])),fill=c,width=1)
for k,(s0,w) in enumerate(SEG):
    s=(s0+w)%PER;dd=np.linspace(0,34.4,30);pts=np.concatenate([P([s],d,zb(d)) for d in dd]);q=T(proj(pts))
    dr.line(q,fill=(255,255,255),width=1);dr.text(q[-1],str(k+1)+':'+str(int(s)),fill=(255,255,255))
im.save('out/ln_'+nm+'.png')
