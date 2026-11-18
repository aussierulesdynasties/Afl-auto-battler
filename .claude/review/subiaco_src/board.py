import sys
from PIL import Image,ImageDraw,ImageFont
ph,ren,ov,out,title=sys.argv[1:6]
P=Image.open(ph).convert('RGB');W,H=P.size
R=Image.open(ren).convert('RGBA').resize((W,H));bg=Image.new('RGBA',(W,H),(40,44,52,255));bg.alpha_composite(R)
O=Image.open(ov).convert('RGB').resize((W,H))
try:F=ImageFont.truetype('arial.ttf',28);F2=ImageFont.truetype('arial.ttf',22)
except:F=F2=ImageFont.load_default()
B=Image.new('RGB',(W*3+40,H+90),(24,26,30));d=ImageDraw.Draw(B)
d.text((10,8),title,font=F,fill=(255,255,255))
for k,(im,lab) in enumerate(((P,'Real photo'),(bg.convert('RGB'),'Our model, same camera'),(O,'Model edges (magenta) over the photo'))):
    B.paste(im,(10+k*(W+10),80));d.text((10+k*(W+10),50),lab,font=F2,fill=(230,230,230))
B.save(out)
