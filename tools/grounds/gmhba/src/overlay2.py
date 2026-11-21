# photo | render | overlay (render at 50% over photo, render edges in red)
import sys
from PIL import Image,ImageFilter,ImageChops
ph=Image.open(sys.argv[3] if len(sys.argv)>3 and sys.argv[3]!='wide' else 'photo.jpg').convert('RGB');rn=Image.open(sys.argv[1]).convert('RGBA');out=sys.argv[2]
bg=Image.new('RGB',ph.size,(30,30,30));bg.paste(rn,(0,0),rn);mod=bg
blend=Image.blend(ph,mod,0.5)
al=rn.split()[3].point(lambda v:255 if v>128 else 0)
ed=mod.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda v:255 if v>40 else 0)
ed=ImageChops.lighter(ed,al.filter(ImageFilter.FIND_EDGES))
ov=ph.copy();ov.paste((255,0,0),(0,0),ed)
if len(sys.argv)>3 and sys.argv[3]=='wide':
    W,H=ph.size;b=Image.new('RGB',(W*3,H));b.paste(ph,(0,0));b.paste(mod,(W,0));b.paste(blend,(2*W,0));b.save(out)
else:
    b=Image.new('RGB',(ph.size[0],ph.size[1]*2));b.paste(blend,(0,0));b.paste(ov,(0,ph.size[1]));b.save(out)
