import numpy as np, json, sys
sys.path.insert(0,'fit'); from cam import *
from PIL import Image, ImageDraw
exec(open('fit/fit_hq3.py').read().split('h0 = [')[0])
H0 = dict(hl=6.28, rl=1.96, ht=8.14, rt=2.35, wl=5.79, w4=8.09, wt=5.73, w8=5.73, oh=1.0, hpe=8.14, hpr=10.5, Dp=10.0, Wp=7.0, sb0=3.7, sb1=6.4, sbz0=1.7, sbz1=3.35)
def lines(Wp=7.0, Dp=10.0):
    H0['Wp'] = Wp; h=[H0[n] for n in NAMES]; hd,S,P=model(h); L=[]
    w8=5.73; L.append([P(8,0,-1,8.14),P(8,w8/2,-1,10.49),P(8,w8,-1,8.14)]); L.append([P(8,w8/2,-1,10.49),P(8,w8/2,8,10.49)])
    L.append([P(9,0,-1,8.14),P(9,Wp,-1,8.14),P(9,Wp,Dp/2,10.49),P(9,Wp,Dp,8.14)]); L.append([P(9,0,Dp/2,10.49),P(9,Wp,Dp/2,10.49)])
    L.append([P(9,0,0,0.9),P(9,0,0,8.14)]); L.append([P(9,Wp,0,0.9),P(9,Wp,0,8.14)])
    return L
def draw(cam, img, box, out, sc, **kw):
    c=json.load(open('fit/'+cam)); im=Image.open(img).convert('RGB'); d=ImageDraw.Draw(im)
    for l in lines(**kw):
        q=proj(c['p'],np.array(l,float),c['W']/2,c['H']/2); d.line([tuple(x) for x in q],fill=(255,0,255),width=2)
    im=im.crop(box); im.resize((int(im.width*sc),int(im.height*sc))).save(out)
if __name__=='__main__':
    kw=json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
    draw('cam_a02s0.json','hunt/a02.jpg',(900,1400,1400,1750),'work/wire_a02.png',2,**kw)
    draw('cam_g34h.json','hunt/g34.jpg',(880,300,1130,450),'work/wire_g34.png',4,**kw)
