# Hand-painted boundary boards for the director's A/B/C choice (read off c07, 2025; lettering only, no logos copied).
# tio_run.png: the blue TIO run, one white TIO box per 3 m.  sponsors.png: the far-side run, laid along arc metres
# 0..60 of fence_hoard from (20,89): Centralian Today x3, bare, navy board (lettering unreadable in c07), Lasseters x4, RED CENTRE.
import os
from PIL import Image,ImageDraw,ImageFont
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','opt');os.makedirs(OUT,exist_ok=True)
PX=100;H=int(0.9*PX)
def font(n,s):return ImageFont.truetype(os.path.join('C:/Windows/Fonts',n),int(s))
# TIO run: 15 boards of 3 m
L=45;im=Image.new('RGBA',(L*PX,H),(29,63,150,255));d=ImageDraw.Draw(im)
for i in range(15):
    cx=int((i*3+1.5)*PX);d.rounded_rectangle((cx-62,12,cx+62,H-12),8,fill=(250,250,250,255))
    d.text((cx,H//2+1),'TIO',font=font('segoeuib.ttf',H*0.55),fill=(29,63,150,255),anchor='mm')
for i in range(1,15):d.line((i*3*PX,0,i*3*PX,H),fill=(18,40,100,255),width=2)   # board joints
im.save(os.path.join(OUT,'tio_run.png'))
# sponsor run (transparent where the fence is bare)
L=60;im=Image.new('RGBA',(L*PX,H),(0,0,0,0));d=ImageDraw.Draw(im)
def board(s0,s1,bg,reps,txt,fn,col,sz):
    d.rectangle((int(s0*PX),0,int(s1*PX)-1,H-1),fill=bg)
    w=(s1-s0)/reps
    for k in range(reps):
        cx=int((s0+w*(k+0.5))*PX)
        if txt:d.text((cx,H//2),txt,font=font(fn,H*sz),fill=col,anchor='mm')
    for k in range(1,reps):d.line((int((s0+w*k)*PX),0,int((s0+w*k)*PX),H),fill=(0,0,0,40),width=2)
board(0,7.5,(246,246,244,255),3,'Centralian Today','georgia.ttf',(40,40,40,255),0.27)
board(37,44.5,(22,30,52,255),3,None,None,None,0)                 # navy board: lettering unreadable in c07
board(44.5,54.5,(246,246,244,255),4,'Lasseters','segoeui.ttf',(120,120,120,255),0.42)
d.rectangle((int(54.5*PX),0,int(60*PX)-1,H-1),fill=(16,16,16,255))
d.text((int(57.25*PX),H//2),'RED',font=font('segoeuib.ttf',H*0.6),fill=(225,40,40,255),anchor='rm')
d.text((int(57.4*PX),H//2),' CENTRE',font=font('segoeuib.ttf',H*0.6),fill=(250,250,250,255),anchor='lm')
im.save(os.path.join(OUT,'sponsors.png'));print('boards painted')
