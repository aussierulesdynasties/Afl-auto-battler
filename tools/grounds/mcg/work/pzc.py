# python work/pzc.py b0 [b0 ...] : photo pano over render pano -> work/pzc<b0>.png (60 deg each)
import sys,os,subprocess
from PIL import Image
for b in sys.argv[1:]:
    b=int(b)
    for img,o in (('ge','work/_pp.png'),('rr','work/_pr.png')):
        subprocess.run([sys.executable,'work/pano.py',str(b),str(b+60),o],env=dict(os.environ,IMG=img),check=True,stdout=subprocess.DEVNULL)
    a,r=Image.open('work/_pp.png'),Image.open('work/_pr.png');c=Image.new('RGB',(a.width,a.height+r.height))
    c.paste(a,(0,0));c.paste(r,(0,a.height));c.save(f'work/pzc{b}.png');print('pzc',b)
