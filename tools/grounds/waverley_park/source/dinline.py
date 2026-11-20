exec(open('pj.py',encoding='utf-8').read())
import sys
from PIL import Image,ImageDraw
ZR_IN,ZR_OUT,DR_IN,DR_OUT=8.9,15.6,19.7,35.2
def zroof(d):return ZR_IN+(ZR_OUT-ZR_IN)*(d-DR_IN)/(DR_OUT-DR_IN)
x0,y0,x1,y1,sc=map(int,sys.argv[1:6])
im=Image.open('ref.jpg').convert('RGB').crop((x0,y0,x1,y1)).resize(((x1-x0)*sc,(y1-y0)*sc),Image.LANCZOS);dr=ImageDraw.Draw(im)
for dd,col in((12,'blue'),(14,'cyan'),(16,'lime'),(18,'yellow'),(19.7,'red')):
    pts=[proj(P([s],dd,zroof(dd))[0])[0] for s in np.arange(150,300,1.0)]
    pts=[((p[0]-x0)*sc,(p[1]-y0)*sc) for p in pts];dr.line(pts,fill=col,width=2)
for s in range(150,300,10):
    p=proj(P([s],19.7,zroof(19.7))[0])[0];dr.text(((p[0]-x0)*sc+3,(p[1]-y0)*sc-12),str(s),fill='white')
im.save('out/din_%d_%d.png'%(x0,y0))
