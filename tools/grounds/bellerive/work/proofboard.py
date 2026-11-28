# python work/proofboard.py review_dir : overlays (GE above, model over GE below) per view, the sign beside its reference, turntable GIF
import sys,os,glob
from PIL import Image,ImageDraw,ImageFont
R=sys.argv[1];f=ImageFont.truetype('arialbd.ttf',26)
def lab(im,s):
    d=ImageDraw.Draw(im);d.rectangle((0,0,len(s)*16+16,36),fill=(0,0,0));d.text((8,4),s,font=f,fill=(255,255,255));return im
for v in ('f000','f090','f135','f180','f225','f270','f315','i030','i180'):
    g=Image.open(f'ge/{v}.png').convert('RGB');r=Image.open(f'rr/{v}.png').convert('RGBA');c=g.copy();c.paste(r,(0,0),r)
    B=Image.new('RGB',(1920,2160));B.paste(lab(g,f'{v}: Google Earth'),(0,0));B.paste(lab(c,f'{v}: model over Google Earth'),(0,1080))
    B.resize((1280,1440),Image.LANCZOS).save(os.path.join(R,f'overlay_{v}.jpg'),quality=88)
s=Image.open('work/sign_ref.png').convert('RGB');m=Image.open(os.path.join(R,'close_sign_tower.png')).convert('RGB')
h=900;s=s.resize((int(s.width*h/s.height),h));m=m.resize((int(m.width*h/m.height),h))
B=Image.new('RGB',(s.width+m.width+20,h),(30,30,30));B.paste(lab(s,'reference (GE x330)'),(0,0));B.paste(lab(m,'model'),(s.width+20,0));B.save(os.path.join(R,'sign_vs_ref.jpg'),quality=90)
fr=[Image.open(p).convert('RGB').resize((640,360)) for p in sorted(glob.glob(os.path.join(R,'turn','f*.png')))]
fr[0].save(os.path.join(R,'turntable.gif'),save_all=True,append_images=fr[1:],duration=120,loop=0)
print('ok',len(fr))
