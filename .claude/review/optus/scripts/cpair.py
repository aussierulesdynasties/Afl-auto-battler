import sys
from PIL import Image,ImageDraw
ph=Image.open('prev/photo_full.png').convert('RGB');md=Image.open(sys.argv[1]).convert('RGBA')
bg=ph.copy();bg.paste(md,(0,0),md);md=bg
S=4;W=80
boxes=[('A',1005,935),('B',1095,865),('C',1170,915),('D',1060,995)]
out=Image.new('RGB',(W*S*2+10,W*S*4+30),'white')
for i,(n,x0,y0) in enumerate(boxes):
  for j,im in enumerate((ph,md)):
    c=im.crop((x0,y0,x0+W,y0+W)).resize((W*S,W*S),Image.NEAREST);d=ImageDraw.Draw(c)
    for k in range(0,W+1,5):
        col=(255,0,255) if k%10==0 else (255,255,0)
        d.line([(k*S,0),(k*S,W*S)],fill=col);d.line([(0,k*S),(W*S,k*S)],fill=col)
        if k%10==0:d.text((k*S+1,1),str(x0+k),fill=(255,0,255));d.text((1,k*S+1),str(y0+k),fill=(255,0,255))
    d.text((W*S-30,W*S-12),n+('ph' if j==0 else 'md'),fill=(255,0,0))
    out.paste(c,(j*(W*S+10),i*(W*S+10)))
out.save(sys.argv[2])
