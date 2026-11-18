from PIL import Image,ImageDraw,ImageFont
R='C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/fervent-kirch-57431f/.claude/review/'
F=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',48)
ph=Image.open('p92.png').convert('RGB');W,H=ph.size
rd=Image.open('out/r92t.png').convert('RGBA').resize((W,H))
bg=Image.new('RGBA',(W,H),(255,0,255,255));bg.alpha_composite(rd);md=bg.convert('RGB')
ov=Image.blend(ph,md,0.5)
def lab(im,t):
    im=im.copy();d=ImageDraw.Draw(im);d.rectangle((0,0,len(t)*30+20,62),fill=(0,0,0));d.text((10,5),t,font=F,fill=(255,255,255));return im
S=Image.new('RGB',(W,H*3))
for i,(im,t) in enumerate(((ph,'photo 1992'),(md,'model'),(ov,'50% overlay'))):S.paste(lab(im,t),(0,H*i))
S.save(R+'waca_vs_photo.png')
P={'north_stand':(460,440,1320,840),'emu_club':(1270,600,2010,920),'far_stands':(1140,400,2280,700),'scoreboard':(860,420,1300,560),'light_towers':(440,40,2320,640)}
for k,b in P.items():
    w,h=b[2]-b[0],b[3]-b[1];s=max(1,min(3,1800//w))
    B=Image.new('RGB',(w*s*3,h*s))
    for i,(im,t) in enumerate(((ph,'photo 1992'),(md,'model'),(ov,'50% overlay'))):
        B.paste(lab(im.crop(b).resize((w*s,h*s),Image.LANCZOS),t),(w*s*i,0))
    B.save(R+'waca_part_%s.png'%k)
print(W,H)
