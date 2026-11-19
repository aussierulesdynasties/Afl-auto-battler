# texture proof board: photo crop | second panel | close shot, one row per surface type
from PIL import Image,ImageDraw,ImageFont
F=ImageFont.truetype('C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/agitated-aryabhata-ac1c0b/assets/fonts/Barlow-SemiBold.ttf',22)
def c(f,b,k=1.0): return Image.open(f).convert('RGB').crop(tuple(int(v*k) for v in b))
def tx(j,m): return Image.open(f'tx/tex_{j}_{m}.png').convert('RGB')
def fit(im,w,h):   # whole image scaled to fit, centred on the board colour (crops keep their shape)
    k=min(w/im.width,h/im.height);p=im.resize((int(im.width*k),int(im.height*k)),Image.LANCZOS)
    o=Image.new('RGB',(w,h),(24,26,30));o.paste(p,((w-p.width)//2,(h-p.height)//2));return o
G=lambda j:('game distance',tx(j,'game'))
CL=lambda j,t='close':(t,tx(j,'close'))
P1=lambda b:('model, p1 camera, same crop',c('ren.png',b))
R=[('concrete (wall)',c('ph/p8.jpg',(0,380,300,620),2000/1280),'p8',[G('concrete'),CL('concrete')]),
   ('cladding (fascia)',c('ph/p13.jpg',(190,280,480,700),2),'p13',[G('cladding'),CL('cladding')]),
   ('roof sheeting, top',c('photo.jpg',(560,395,720,450)),'p1',[G('roof_top'),CL('roof_top')]),
   ('roof sheeting, underside',c('ph/p13.jpg',(560,0,760,200),2),'p13',[G('roof_under'),CL('roof_under')]),
   ('seats (empty, no crowd)',c('ph/p12.jpg',(0,0,2560,1440)),'p12',[G('seats'),CL('seats_row','seat height, across the tier')]),
   ('painted steel (tower)',c('ph/p11.jpg',(120,0,240,440),2),'p11',[G('steel_tower'),CL('steel_tower')]),
   ('navy steel (columns)',c('photo.jpg',(925,512,985,572)),'p1',[P1((925,512,985,572)),CL('steel_navy','free camera, 4 m')]),
   ('deck (roof terrace)',c('photo.jpg',(255,412,345,457)),'p1',[P1((255,412,345,457)),CL('deck','free camera, 3 m above')]),
   ('soffit (west canopy underside)',c('photo.jpg',(900,500,1010,555)),'p1',[P1((900,500,1010,555)),CL('soffit','free camera, 2.5 m below')])]
H=300;W=1600;Gp=8;T=34;PW=533;QW=W-2*PW-4*Gp
bd=Image.new('RGB',(W,len(R)*(H+T+Gp)+Gp),(24,26,30));d=ImageDraw.Draw(bd);y=Gp
for name,ph,src,pan in R:
    d.text((Gp,y+4),f'{name}   photo {src}  |  {pan[0][0]}  |  {pan[1][0]}',font=F,fill=(235,235,235));y+=T
    bd.paste(fit(ph,QW,H),(Gp,y));x=W-2*PW-Gp
    for lab,im in pan:
        bd.paste(fit(im,PW,H) if lab.startswith('model') else im.resize((PW,H)),(x,y));x+=PW+Gp
    y+=H+Gp
bd.save('texture_board.png');print(bd.size)
