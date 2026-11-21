# For each facade material: the view where it shows most, photo crop above render crop (bbox of its ID mask + margin).
# python work/facboard.py <render_dir> <out.png> [idDir]
import sys,os,json,glob,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from idname import table
from PIL import Image,ImageDraw
rdir=sys.argv[1];out=sys.argv[2];idd=sys.argv[3] if len(sys.argv)>3 else 'rf/id16'
nl=sorted(f[:-4] for f in os.listdir('model/tex') if f.startswith('fac_') and f.endswith('.png'))
T=table(nl);best={}
for f in sorted(glob.glob(idd+'/*.png')):
    v=os.path.basename(f)[:-4];r=np.asarray(Image.open(f).convert('RGBA')).astype(float)
    for n in nl:
        m=(np.abs(r[:,:,:3]-T[n]).sum(2)<5)&(r[:,:,3]>250);s=int(m.sum())
        if s>best.get(n,(0,))[0]:
            ys,xs=np.nonzero(m);best[n]=(s,v,(int(np.percentile(xs,2)),int(np.percentile(ys,2)),int(np.percentile(xs,98)),int(np.percentile(ys,98))))
tiles=[]
for n in nl:
    if n not in best:continue
    s,v,(x0,y0,x1,y1)=best[n];mx=max(20,(x1-x0)//6);box=(max(0,x0-mx),max(0,y0-mx),min(1920,x1+mx),min(1080,y1+mx))
    ph=Image.open('ge/%s.png'%v).convert('RGB').crop(box);r=Image.open('%s/%s.png'%(rdir,v)).convert('RGBA');bg=Image.new('RGBA',r.size,(0,0,0,255));bg.alpha_composite(r)
    rc=bg.convert('RGB').crop(box);w=420;h=int(w*(box[3]-box[1])/(box[2]-box[0]));h=min(h,300)
    t=Image.new('RGB',(w,2*h+18),(20,20,20));t.paste(ph.resize((w,h)),(0,18));t.paste(rc.resize((w,h)),(0,18+h));ImageDraw.Draw(t).text((4,3),'%s  %s'%(n,v),fill=(255,255,0));tiles.append(t)
W=4;rows=[tiles[i:i+W] for i in range(0,len(tiles),W)];H=sum(max(t.size[1] for t in r) for r in rows)
B=Image.new('RGB',(W*424,H),(0,0,0));y=0
for r in rows:
    for i,t in enumerate(r):B.paste(t,(i*424,y))
    y+=max(t.size[1] for t in r)
B.save(out);print(B.size,{n:best[n][1] for n in best})
