import sys;camf,out=sys.argv[1],sys.argv[2];sys.argv=['x']
exec(open('tools/fitcam.py').read().split("if __name__")[0])
from PIL import Image,ImageDraw
c=json.load(open(camf));p=np.array(c['p'])
im=Image.open('photos/crop.jpg').convert('RGB');d=ImageDraw.Draw(im)
col={'4681536':(255,255,0),'111572163':(0,255,255),'271422946':(255,0,255),'271422949':(255,128,0),'191661675':(0,255,0),'621876938':(255,0,0),'621879217':(255,80,80),'621895966':(200,0,0),'1051207116':(255,255,255)}
hz={'621876938':12,'621879217':40,'621895966':12}
for k,cc in col.items():
    pts=G['ways'][k];X=np.array([(x,y,hz.get(k,0)) for x,y in pts]);Y=proj(p,X)
    d.line([tuple(q) for q in Y],fill=cc,width=2)
for t in OT:
    a=proj(p,np.array([(*TW[t],0),(*TW[t],60)]));d.line([tuple(a[0]),tuple(a[1])],fill=(255,0,0),width=2);d.text(tuple(a[1]),str(t)[-2:],fill=(255,255,0))
for q in GR:d.ellipse([q[0]-3,q[1]-3,q[0]+3,q[1]+3],outline=(0,0,255))
im.save(out)
