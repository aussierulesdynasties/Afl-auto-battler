# each sign: reference photo p1 crop | same crop of the model rendered through the fitted p1 camera
from PIL import Image,ImageDraw,ImageFont
F=ImageFont.truetype('C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/agitated-aryabhata-ac1c0b/assets/fonts/Barlow-SemiBold.ttf',22)
ph=Image.open('photo.jpg').convert('RGB');r=Image.open('ren.png');rn=Image.new('RGB',r.size);rn.paste(r,mask=r.split()[3])
S=[('GMHBA STADIUM, wedge front',(295,488,372,528)),('Geelong Cats crest, Premiership Stand',(470,470,550,560)),
   ('PREMIERSHIP STAND band',(580,552,694,580)),('gmhba STADIUM, roof front',(645,272,740,296))]
CW=760;G=8;T=34;rows=[]
for n,b in S:
    w,h=b[2]-b[0],b[3]-b[1];k=CW/w;rows.append((n,b,int(h*k)))
bd=Image.new('RGB',(2*CW+3*G,sum(T+h+G for *_,h in rows)+G),(24,26,30));d=ImageDraw.Draw(bd);y=G
for n,b,h in rows:
    d.text((G,y+4),n+'   photo p1  |  model through the p1 camera',font=F,fill=(235,235,235));y+=T
    for i,im in enumerate((ph,rn)):bd.paste(im.crop(b).resize((CW,h),Image.LANCZOS),(G+i*(CW+G),y))
    y+=h+G
bd.save('signs_board.png');print(bd.size)
