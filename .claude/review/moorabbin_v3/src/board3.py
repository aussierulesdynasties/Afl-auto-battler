import json,numpy as np,sys
exec(open('meas.py').read())
from PIL import Image,ImageDraw,ImageFont
f=ImageFont.truetype('arial.ttf',20);fs=ImageFont.truetype('arial.ttf',16)
a=Image.open('A.jpg').convert('RGB');r=Image.open('render3_cam.png').convert('RGB')
assert r.size==a.size,(r.size,a.size)
ov=Image.blend(a,r,0.5);W,H=a.size
B=Image.new('RGB',(W*3+40,H+50),(20,20,24));d=ImageDraw.Draw(B)
for i,(im,t) in enumerate([(a,'Photo: Austadiums aerial ("2006 Aerial view", file aerial-97), 1024x576 full size'),(r,'Model from the matched camera'),(ov,'50% overlay')]):
    B.paste(im,(10+i*(W+10),40));d.text((10+i*(W+10),10),t,fill=(240,240,240),font=fs)
B.save('proof/overlay_full.png')
O=json.load(open('build.json'))
def box(P,pad=12):
    q=np.array([pr(p)[0] for p in P]);x0,y0=q.min(0)-pad;x1,y1=q.max(0)+pad
    return (max(0,int(x0)),max(0,int(y0)),min(W,int(x1)),min(H,int(y1)))
sf=O['stand']['front'];sr=O['stand']['rear'];hs=O['stand']['h']
parts=[('Long stand: seats and rake',[[x,y,0] for x,y in sf]+[[x,y,8] for x,y in sr]),
 ('Long stand: roof',[[x,y,hs] for x,y in sf+sr]),
 ('G.G. Huggins Stand: facade and tiers',[[-19,93.1,0],[-67.1,67.6,0],[-19,93.1,14],[-67.1,67.6,14],[-25,78,0],[-70,55,0]]),
 ('Club buildings behind the Huggins',[[x,y,0] for b in O['club'] for x,y in b['pts']]+[[x,y,b['h']] for b in O['club'] for x,y in b['pts']]),
 ('Scoreboard',[[*O['score']['ends'][0],0],[*O['score']['ends'][1],O['score']['top']]]),
 ('Light towers (two)',[[*O['poles']['P6'][0],0],[*O['poles']['P6'][0],O['poles']['P6'][1]],[*O['poles']['P7'][0],0],[*O['poles']['P7'][0],O['poles']['P7'][1]]]),
 ('Terraces and boundary',[[-31,-93,0],[52,-68,0],[30,-60,0],[0,-80,4]])]
rows=[]
for t,P in parts:
    bx=box(P);s=max(1,min(5,700//max(1,bx[2]-bx[0])));pa=a.crop(bx);pb=r.crop(bx)
    sz=(pa.width*s,pa.height*s);rows.append((t,pa.resize(sz,Image.LANCZOS),pb.resize(sz,Image.LANCZOS)))
wmax=max(x[1].width for x in rows);Ht=sum(x[1].height+40 for x in rows)
C=Image.new('RGB',(wmax*2+30,Ht+10),(20,20,24));d=ImageDraw.Draw(C);y=5
for t,pa,pb in rows:
    d.text((10,y),t+'  (left: photo crop, right: model, same camera)',fill=(240,240,240),font=fs);C.paste(pa,(10,y+30));C.paste(pb,(20+wmax,y+30));y+=pa.height+40
C.save('proof/parts_board.png');print(C.size)
