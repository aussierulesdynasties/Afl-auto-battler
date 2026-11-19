# texture close-ups beside photo crops, with the grey stddev each image measures as used in the model (chk/texstd.json)
import json
from PIL import Image,ImageDraw,ImageFont
f=ImageFont.truetype('arial.ttf',18);fs=ImageFont.truetype('arial.ttf',14)
G='dl/moorabbin-old-grandstands1.jpg';P93='dl/moorabbin-1993-last-game.jpg'
ROWS=[('plastic','Moulded seats (3D): Huggins blue front tier, Huggins and pavilion green tiers, empty',[(G,(300,395,600,480)),(G,(420,280,700,330))]),
 ('timber','Long-stand benches (3D): painted timber slats',[('dl/moorabbin-old-grandstands3.jpg',(560,330,760,470))]),
 ('concrete','Steps, walkways, aprons',G,(0,415,150,520)),
 ('white','Painted walls and fascias',G,(480,335,630,385)),
 ('glass','Glazing behind the tiers',G,(310,75,520,140)),
 ('brown_roof','Huggins roof',G,(300,30,800,80)),
 ('roof_deck','Sheet roofs (pavilion, sawtooth, long stand)',G,(800,215,1150,280)),
 ('brick_win','Brick blocks with windows',G,(950,375,1200,430)),
 ('park_grass','Grass on the bank tops and behind the banks',[('hb/moo-3-goals.jpg',(1080,1288,1340,1340))]),
 ('steel','Light towers, posts (galvanised fence post; light tower)',[('hb/moo-5-keep-off.jpg',(1270,760,1420,1260)),('dl/200503-Moorabbin2.jpg',(270,10,350,300)),('dl/200503-Moorabbin2.jpg',(285,10,335,90))]),
 ('chainwire','Crest chain-wire fence',P93,(150,470,450,560))]
S={r[0].replace('.png',''):r for r in json.load(open('chk/texstd.json'))}
H=200;W=1260;B=Image.new('RGB',(W,40+len(ROWS)*(H+34)),(20,20,24));d=ImageDraw.Draw(B)
d.text((10,10),'Hand-made textures (no photo pixels) beside photo crops of the real surface. std = grey stddev 0-255 as used in the model.',fill=(240,240,240),font=fs)
y=40
for r in ROWS:
    n,lab=r[0],r[1];crops=r[3] if len(r)==4 and not isinstance(r[2],str) else ([(r[2],r[3])] if len(r)==4 else r[2])
    t=Image.open('hand/'+n+'.png').convert('RGB');t=t.crop((0,0,min(t.size[0],512),min(t.size[1],512))).resize((H*t.size[0]//t.size[1] if t.size[1]<t.size[0]*3 else H,H))
    t=t.crop((0,0,min(t.size[0],560),H))
    ps=[Image.open(sr).convert('RGB').crop(bx) for sr,bx in crops];ps=[q.resize((max(1,q.size[0]*H//q.size[1]),H)) for q in ps]
    p=Image.new('RGB',(sum(q.size[0]+6 for q in ps),H),(20,20,24));xx=0
    for q in ps:p.paste(q,(xx,0));xx+=q.size[0]+6
    p=p.crop((0,0,min(p.size[0],600),H))
    tints=[k for k in S if k.startswith(n)]
    st=', '.join('%s %.1f'%(k.replace(n,'').strip('_') or 'base',S[k][1]) for k in tints)
    d.text((10,y),'%s: %s   |  std: %s'%(n,lab,st),fill=(255,220,120),font=fs)
    B.paste(t,(10,y+20));B.paste(p,(600,y+20));y+=H+34
B.save('proof/texture_sheet.png');print(B.size)
