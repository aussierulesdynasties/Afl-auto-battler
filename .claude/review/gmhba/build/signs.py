# Hand-drawn signs for the GMHBA exterior (no photo pixels): Cats logo, GMHBA Stadium sign, Premiership Stand band, scoreboard
from PIL import Image,ImageDraw,ImageFont
F='C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/agitated-aryabhata-ac1c0b/assets/fonts/'   # Barlow, SIL OFL 1.1 (repo copy)
NAVY=(28,42,92);WHITE=(246,246,244);SKY=(92,196,236);RED=(214,32,38)
def font(n,s):return ImageFont.truetype(F+n,s)
def ctext(d,cx,y,t,f,fill,stretch=None):
    w=d.textlength(t,font=f);d.text((cx-w/2,y),t,font=f,fill=fill)
def cats(w,h):
    # Geelong crest traced by hand on the p1 grid (crest2.py)
    from crest2 import cats_p1
    return cats_p1(w,h,NAVY,WHITE,font)
def gmhba(w,h):
    im=Image.new('RGBA',(840,360),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle([20,40,130,150],12,fill=SKY);d.rectangle([62,60,88,130],fill=WHITE);d.rectangle([40,82,110,108],fill=WHITE)
    d.text((150,10),'gmhba',font=font('Barlow-SemiBold.ttf',170),fill=SKY,stroke_width=7,stroke_fill=SKY)
    d.text((240,190),'STADIUM',font=font('BarlowCondensed-Bold.ttf',150),fill=WHITE)
    im=im.crop(im.getbbox())   # the sign's own letters fill the measured box (p1 x 306-368)
    return im.resize((w,h),Image.LANCZOS)
def band(w,h,t='PREMIERSHIP STAND'):
    # p1: the white letters run the full length of the navy band
    im=Image.new('RGB',(w*4,h*4),NAVY);f=font('Barlow-SemiBold.ttf',200);tw=int(ImageDraw.Draw(im).textlength(t,font=f))
    tl=Image.new('RGBA',(tw+20,300),(0,0,0,0));ImageDraw.Draw(tl).text((0,0),t,font=f,fill=WHITE);tl=tl.crop(tl.getbbox())
    tl=tl.resize((int(w*4*0.94),int(h*4*0.72)),Image.LANCZOS);im=im.convert('RGBA');im.alpha_composite(tl,(int(w*4*0.03),int(h*4*0.14)))
    return im.convert('RGB').resize((w,h),Image.LANCZOS)
def screen(w,h):
    # p1: red frame (about 0.6 m of an 18.1 x 9.6 m board) with white lettering top and bottom (unreadable at photo
    # scale: drawn as white letter bars)
    import random;R=random.Random(7);W,H=w*2,h*2;b=int(H*0.085)
    im=Image.new('RGB',(W,H),RED);d=ImageDraw.Draw(im)
    d.rectangle([int(W*0.035),b,W-int(W*0.035),H-b],fill=(28,30,36))
    # screen switched off (no crowd picture: director 2026-11-19 no simulated crowd): LED modules about 0.96 m
    x0,x1=int(W*0.035),W-int(W*0.035);mp=max(8,int((x1-x0)/19))
    for x in range(x0,x1,mp):d.line([(x,b),(x,H-b)],fill=(40,43,50),width=2)
    for y in range(b,H-b,mp):d.line([(x0,y),(x1,y)],fill=(40,43,50),width=2)
    bh=int(b*0.45);bw=int(b*0.5)
    for x in range(int(W*0.08),W-int(W*0.12),int(W*0.22)):
        for y in ((b-bh)//2,H-b+(b-bh)//2):
            pass   # lettering left out (director 2026-11-18 "C: no lettering"): blank red frame
    return im.resize((w,h),Image.LANCZOS)

def roofsign(W,H,split):
    # p1 roof-front sign: white "gmhba" with its cross mark on the cyan panel, white STADIUM letters on the grey
    im=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(im);m=int(H*0.16);hh=H-2*m
    d.rounded_rectangle([m*3,m,m*3+hh,m+hh],int(hh*0.12),outline=WHITE,width=max(3,hh//10))
    cx=m*3+hh//2;cy=m+hh//2;t=hh//7;r=int(hh*0.32);d.rectangle([cx-t,cy-r,cx+t,cy+r],fill=WHITE);d.rectangle([cx-r,cy-t,cx+r,cy+t],fill=WHITE)
    f=font('Barlow-SemiBold.ttf',int(H*0.95));x0=m*3+hh+m*2;w=d.textlength('gmhba',font=f)
    tmp=Image.new('RGBA',(int(w)+10,int(H*1.3)),(0,0,0,0));ImageDraw.Draw(tmp).text((0,0),'gmhba',font=f,fill=WHITE,stroke_width=max(2,H//40),stroke_fill=WHITE);tmp=tmp.crop(tmp.getbbox())
    tmp=tmp.resize((split-x0-m*3,hh),Image.LANCZOS);im.alpha_composite(tmp,(x0,m))
    f2=font('BarlowCondensed-Bold.ttf',int(H));tmp=Image.new('RGBA',(int(d.textlength('STADIUM',font=f2))+10,int(H*1.3)),(0,0,0,0))
    ImageDraw.Draw(tmp).text((0,0),'STADIUM',font=f2,fill=WHITE);tmp=tmp.crop(tmp.getbbox());tmp=tmp.resize((W-split-m*4,hh),Image.LANCZOS)
    im.alpha_composite(tmp,(split+m*2,m));return im
