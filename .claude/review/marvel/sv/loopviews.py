# Pick 2019-06 loop panos every ~15 m, fetch at zoom 3, render a flat view facing the wall (toward stadium centre).
import sys,os,json,math,numpy as np
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));__file__=os.path.join(HERE,'sv.py')
exec(open(os.path.join(HERE,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
sys.path.insert(0,HERE);from persp import render
from PIL import Image,ImageDraw
db=json.load(open(os.path.join(HERE,'panos.json')))
L=[(k,v) for k,v in db.items() if v.get('date')=='2019-06' and 's' in v]
ang=lambda v:math.atan2(-v['t'],-v['s'])    # bearing round the centre
L.sort(key=lambda kv:ang(kv[1]))
pick=[];last=None
for k,v in L:
    p=np.array([v['s'],v['t']])
    if last is None or np.linalg.norm(p-last)>=15:pick.append((k,v));last=p
os.makedirs(os.path.join(HERE,'loop'),exist_ok=True);rows=[]
for n,(k,v) in enumerate(pick):
    f=os.path.join(HERE,'loop',k+'_z3.jpg')
    if not os.path.exists(f):fetch(k,3,f)
    # world heading toward centre: local -> world vector
    w0=wld(v['s'],v['t'])[:2];w1=wld(0,0)[:2];d=w1-w0;hd=math.degrees(math.atan2(d[0],d[1]))
    im=render(Image.open(f).convert('RGB'),v['h'],v['p'],v['r'],hd,12,100,800,600)
    out=os.path.join(HERE,'loop','v%02d_%s.jpg'%(n,k));im.save(out,quality=90)
    rows.append(dict(n=n,id=k,s=v['s'],t=v['t'],hd=round(hd,1),file=out));print(n,k,v['s'],v['t'],flush=True)
json.dump(rows,open(os.path.join(HERE,'loop','index.json'),'w',newline=''),indent=0)
# contact sheets of 12
for b in range(0,len(rows),12):
    S=Image.new('RGB',(4*400,3*330),'white');dr=ImageDraw.Draw(S)
    for i,r in enumerate(rows[b:b+12]):
        x,y=400*(i%4),330*(i//4);S.paste(Image.open(r['file']).resize((400,300)),(x,y))
        dr.text((x+4,y+302),'v%02d s=%.0f t=%.0f hd=%.0f'%(r['n'],r['s'],r['t'],r['hd']),fill='black')
    S.save(os.path.join(HERE,'loop','sheet%d.jpg'%(b//12)))
