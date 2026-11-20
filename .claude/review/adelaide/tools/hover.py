import sys;ways=sys.argv[1].split(',');hs=[float(x) for x in sys.argv[2].split(',')];out=sys.argv[3];crop=[int(v) for v in sys.argv[4].split(',')];sys.argv=['x']
exec(open('tools/fitcam.py').read().split("if __name__")[0])
from PIL import Image,ImageDraw
p=np.array(json.load(open('cam.json'))['p'])
im=Image.open('photos/crop.jpg').convert('RGB');d=ImageDraw.Draw(im)
cols=[(255,0,0),(255,160,0),(255,255,0),(0,255,0),(0,255,255),(0,80,255),(255,0,255)]
for w in ways:
    for i,h in enumerate(hs):
        X=np.array([(x,y,h) for x,y in G['ways'][w]]);d.line([tuple(q) for q in proj(p,X)],fill=cols[i%7],width=1)
im=im.crop(crop);im=im.resize((im.width*2,im.height*2));d=ImageDraw.Draw(im)
for i,h in enumerate(hs):d.text((10,10+14*i),'%g m'%h,fill=cols[i%7])
im.save(out)
