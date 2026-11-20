# per-part crop board: 1984 photo | matched render | 50% overlay, each part's projected box, 4x
import json,numpy as np,sys
from PIL import Image,ImageDraw
sys.path.insert(0,'.');from cam import proj
D='C:/Users/DANTE/AppData/Local/Temp/claude/b11ecf2cca45cfb5/002c0964-89cd-46e5-bf30-bd32e1451dbd/scratchpad/wh/'
p=json.load(open(D+'cam84.json'))['p'];W=json.load(open(D+'world.json'))
ph=Image.open(D+'bb1984.jpg').convert('RGB');rd=Image.open(D+'rend.png').convert('RGB').resize(ph.size);bl=Image.blend(ph,rd,0.5)
G=[('Reynolds Stand',['reyn_roof','reyn_back']),('Hird Stand',['hird']),('Cookson Pavilion',['cook_roof','cook_seats']),
('North stand and buildings',['n_stand','nb1','nb2']),('Showers stand',['showers_roof']),('Clubrooms, NW building',['club','nw_bldg']),
('Crichton stand, south terrace',['crichton']),('Scoreboard and huts',['scoreboard','sb_hut','sb1','sb2','sb3']),
('East hill',['hill_outer']),('Bowls greens',['bowl1','bowl2']),('NE terrace, croquet hut',['ne_terr_in','croq_hut'])]
rows=[];S=4
for name,ks in G:
    X=[]
    for k in ks:
        for q in W[k]['pts']: X+=[[q[0],q[1],0],[q[0],q[1],W[k].get('h',0) or 0]]
    u=proj(p,np.array(X,float));x0,y0=np.floor(u.min(0)-14);x1,y1=np.ceil(u.max(0)+14)
    b=(int(max(0,x0)),int(max(0,y0)),int(min(ph.width,x1)),int(min(ph.height,y1)))
    cs=[im.crop(b).resize(((b[2]-b[0])*S,(b[3]-b[1])*S),Image.LANCZOS) for im in (ph,rd,bl)]
    rows.append((name,cs))
w=max(sum(c.width for c in cs)+40 for _,cs in rows);h=sum(cs[0].height+34 for _,cs in rows)
o=Image.new('RGB',(w,h),(24,24,24));d=ImageDraw.Draw(o);y=0
for name,cs in rows:
    d.text((8,y+8),name+'   (1984 photo | render | 50% overlay)',fill=(240,240,240));y+=30;x=0
    for c in cs: o.paste(c,(x,y));x+=c.width+20
    y+=cs[0].height+4
o.save(D+'crops.png');print('CROPS',o.size)
