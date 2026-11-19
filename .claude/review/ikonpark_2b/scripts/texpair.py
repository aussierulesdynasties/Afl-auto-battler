# texture board: each painted texture beside the photo crop it copies. usage: texpair.py TEXDIR REF94 REFI2 OUT
import sys;from PIL import Image,ImageDraw
T,P94,PI2,OUT=sys.argv[1:5];A=Image.open(P94).convert('RGB');B=Image.open(PI2).convert('RGB')
st=dict(l.split()[:2] for l in open(T+'/stddev.txt'))
# (material, photo, crop box, what the crop shows)
C=[('seats','I2',(620,292,900,345),'far stand blue seats (empty)'),('seatslegends','I2',(20,290,240,345),'Legends seats'),
   ('roof','94',(250,88,450,128),'Heroes wave roof sheet'),('greyroof','94',(580,215,640,255),'Fosters roof'),('roofgrey','I2',(540,238,1030,285),'Legends/Pratt roof edge'),
   ('under','I2',(320,252,1000,302),'roof underside'),('brick','94',(210,395,360,440),'bottom stand brick base'),('timber','94',(215,370,500,400),'bottom stand timber facade'),
   ('wood','94',(75,300,140,350),'west timber paling fence'),('concrete','I2',(867,602,1200,650),'concrete steps'),('terrace','94',(135,340,210,370),'open terrace steps'),
   ('steel','I2',(915,518,1190,566),'steel rail and posts'),('steeldark','I2',(0,247,240,289),'dark steel of the Legends end'),('glassdark','I2',(933,325,1047,373),'NO ERA PHOTO: nearest glazing (modern box)'),
   ('white','I2',(940,349,1035,367),'white cladding'),('red','94',(0,0,1,1),'NO PHOTO: Gardiner band colour (crowd hides it in 1994)')]
W=1500;rh=150;o=Image.new('RGB',(W,rh*((len(C)+1)//2)),(24,24,24));d=ImageDraw.Draw(o)
for i,(m,p,b,txt) in enumerate(C):
    x=(i%2)*750;y=(i//2)*rh
    o.paste(Image.open(f'{T}/{m}.png').convert('RGB').resize((140,140)),(x+5,y+5))
    cr=(A if p=='94' else B).crop(b);s=min(280/cr.width,140/cr.height);o.paste(cr.resize((int(cr.width*s),int(cr.height*s))),(x+150,y+5))
    d.text((x+440,y+10),m,fill=(255,255,0));d.text((x+440,y+30),f'painted stddev {st.get(m,"?")}',fill=(255,255,255))
    d.text((x+440,y+50),f'photo: {"1994 aerial" if p=="94" else "ikon-park-2"} {b}',fill=(200,200,200));d.text((x+440,y+70),txt,fill=(200,200,200))
o.save(OUT,quality=90)
