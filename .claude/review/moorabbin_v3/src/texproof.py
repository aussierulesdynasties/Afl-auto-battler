# texture close-ups beside photo crops, with the grey stddev each image measures as used in the model (chk/texstd.json)
import json
from PIL import Image,ImageDraw,ImageFont
f=ImageFont.truetype('arial.ttf',18);fs=ImageFont.truetype('arial.ttf',14)
G='dl/moorabbin-old-grandstands1.jpg';P93='dl/moorabbin-1993-last-game.jpg'
ROWS=[('blue_seat','Huggins front tier: blue seats, empty',G,(300,395,600,480)),
 ('green_seat','Huggins middle/upper tiers, pavilion: green seats, empty',G,(420,280,700,330)),
 ('concrete','Steps, walkways, aprons',G,(0,415,150,520)),
 ('white','Painted walls and fascias',G,(480,335,630,385)),
 ('glass','Glazing behind the tiers',G,(310,75,520,140)),
 ('brown_roof','Huggins roof',G,(300,30,800,80)),
 ('roof_deck','Sheet roofs (pavilion, sawtooth, long stand)',G,(800,215,1150,280)),
 ('brick_win','Brick blocks with windows',G,(950,375,1200,430)),
 ('park_grass','Grass behind the banks',P93,(1300,470,1600,560)),
 ('steel','Light towers, posts',P93,(1900,130,1935,330)),
 ('chainwire','Crest chain-wire fence',P93,(150,470,450,560))]
S={r[0].replace('.png',''):r for r in json.load(open('chk/texstd.json'))}
H=200;W=1260;B=Image.new('RGB',(W,40+len(ROWS)*(H+34)),(20,20,24));d=ImageDraw.Draw(B)
d.text((10,10),'Hand-made textures (no photo pixels) beside photo crops of the real surface. std = grey stddev 0-255 as used in the model.',fill=(240,240,240),font=fs)
y=40
for n,lab,src,box in ROWS:
    t=Image.open('hand/'+n+'.png').convert('RGB');t=t.crop((0,0,min(t.size[0],512),min(t.size[1],512))).resize((H*t.size[0]//t.size[1] if t.size[1]<t.size[0]*3 else H,H))
    t=t.crop((0,0,min(t.size[0],560),H))
    p=Image.open(src).convert('RGB').crop(box);p=p.resize((max(1,p.size[0]*H//p.size[1]),H));p=p.crop((0,0,min(p.size[0],600),H))
    tints=[k for k in S if k.startswith(n)]
    st=', '.join('%s %.1f'%(k.replace(n,'').strip('_') or 'base',S[k][1]) for k in tints)
    d.text((10,y),'%s: %s   |  std: %s'%(n,lab,st),fill=(255,220,120),font=fs)
    B.paste(t,(10,y+20));B.paste(p,(600,y+20));y+=H+34
B.save('proof/texture_sheet.png');print(B.size)
