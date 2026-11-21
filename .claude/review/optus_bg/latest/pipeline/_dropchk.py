import json, numpy as np
import json as _j; _B=_j.load(open("data/optus/prep/forecourt.json")); X0=_B["x0"]; Y1=_B["y1"]
from PIL import Image, ImageDraw
from skimage import color
F=np.asarray(Image.open('data/optus/prep/forecourt.png')).astype(float); H,W=F.shape[:2]
A=np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB'))
v2=json.load(open('spec/optus_fc_hand.json.v2'))['bands']; cur=json.load(open('spec/optus_fc_hand.json'))
keep={json.dumps(b['pts'][:3]) for b in cur['bands']}
LAWN=np.array(json.load(open('spec/optus.json'))['palette']['lawn'],float); BED=np.array([74,58,44.])
def cls(px):
    if px[3]<128: return 'bare'
    d={'lawn':np.abs(px[:3]/LAWN-1).max(),'bed':np.abs(px[:3]/BED-1).max()}
    k=min(d,key=d.get); return k if d[k]<0.15 else 'paving'
rows=[]
for i,b in enumerate(v2):
    if json.dumps(b['pts'][:3]) in keep: continue
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon([((x-X0)/.1,(Y1-y)/.1) for x,y in b['pts']],fill=1); m=np.asarray(m)>0
    if not m.any(): continue
    c=[cls(p) for p in F[m][::7]]; n=len(c); sh={k:round(100*c.count(k)/n) for k in ('paving','lawn','bed','bare')}
    am=Image.new('L',A.shape[1::-1],0); ImageDraw.Draw(am).polygon([((x-80)/.125,(135-y)/.125) for x,y in b['pts']],fill=1); am=np.asarray(am)>0
    lab=np.median(color.rgb2lab(A[am][None]/255.)[0],0).round(0) if am.any() else None
    rows.append((i,int(m.sum()*.01),sh,lab))
for r in rows: print(r)
print(len(rows))
# contact sheet: per field, aerial crop | model composite crop, field outlined, plus inside-outline share
T=Image.open('_topchk.jpg')  # not used
Aim=Image.open('data/optus/sat_hi_plaza.png').convert('RGB')
G=Image.open('data/optus/prep/ground.png').convert('RGB'); Fim=Image.open('data/optus/prep/forecourt.png')
om=Image.new('L',(W,H),0); ImageDraw.Draw(om).polygon([((x-X0)/.1,(Y1-y)/.1) for x,y in cur['outline']],fill=1); om=np.asarray(om)>0
tiles=[]
for i,b in enumerate(v2):
    if json.dumps(b['pts'][:3]) in keep: continue
    p=np.array(b['pts'],float); cx,cy=p.mean(0); r=max(12,(p.max(0)-p.min(0)).max()/2+6)
    box=(cx-r,cy+r,cx+r,cy-r)
    a=Aim.crop(((box[0]-80)/.125,(135-box[1])/.125,(box[2]-80)/.125,(135-box[3])/.125)).resize((240,240))
    g=G.crop(((box[0]+1500)/1.5,(1500-box[1])/1.5,(box[2]+1500)/1.5,(1500-box[3])/1.5)).resize((240,240),Image.BILINEAR)
    f=Fim.crop(((box[0]-X0)/.1,(Y1-box[1])/.1,(box[2]-X0)/.1,(Y1-box[3])/.1)).resize((240,240)); g.paste(f,(0,0),f)
    pts=[((x-box[0])/(2*r)*240,(box[1]-y)/(2*r)*240) for x,y in p]
    for im in (a,g): ImageDraw.Draw(im).line(pts+pts[:1],fill=(0,200,255),width=2)
    m=Image.new('L',(W,H),0); ImageDraw.Draw(m).polygon([((x-X0)/.1,(Y1-y)/.1) for x,y in b['pts']],fill=1); m=np.asarray(m)>0
    ins=round(100*(m&om).sum()/max(1,m.sum()))
    t=Image.new('RGB',(480,256),(0,0,0)); t.paste(a,(0,16)); t.paste(g,(240,16)); ImageDraw.Draw(t).text((4,2),f'D{i} in-outline {ins}%',fill=(255,255,0)); tiles.append(t)
for k in range(0,len(tiles),12):
    s=Image.new('RGB',(480*3,256*4))
    for j,t in enumerate(tiles[k:k+12]): s.paste(t,((j%3)*480,(j//3)*256))
    s.save(f'_drop_{k//12}.jpg',quality=85)
