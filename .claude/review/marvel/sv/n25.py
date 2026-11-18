import sys,os,json,math
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));__file__=os.path.join(HERE,'sv.py')
exec(open(os.path.join(HERE,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
sys.path.insert(0,HERE);from persp import render
from PIL import Image,ImageDraw
db=json.load(open(os.path.join(HERE,'panos.json')))
L=[(k,v) for k,v in db.items() if v.get('date','').startswith('2025') and 's' in v and v.get('d',99)<60]
os.makedirs('n25',exist_ok=True);rows=[]
for k,v in L:
    f=os.path.join('n25',k+'_z3.jpg')
    if not os.path.exists(f):fetch(k,3,f)
    w0=wld(v['s'],v['t'])[:2];w1=wld(0,0)[:2];d=w1-w0;hd=math.degrees(math.atan2(d[0],d[1]))
    im=render(Image.open(f).convert('RGB'),v['h'],v['p'],v['r'],hd,10,90,800,600)
    o=os.path.join('n25','v_%s.jpg'%k);im.save(o,quality=90);rows.append((v['s'],v['t'],o,v['date']))
rows.sort(key=lambda r:math.atan2(-r[1],-r[0]))
for b in range(0,len(rows),12):
    S=Image.new('RGB',(1600,990),'white');dr=ImageDraw.Draw(S)
    for i,r in enumerate(rows[b:b+12]):
        x,y=400*(i%4),330*(i//4);S.paste(Image.open(r[2]).resize((400,300)),(x,y))
        dr.text((x+4,y+302),'s=%.0f t=%.0f %s'%(r[0],r[1],r[3]),fill='black')
    S.save('n25/sheet%d.jpg'%(b//12))
print(len(rows))
