from PIL import Image,ImageDraw
ph=Image.open('../main.jpg').convert('RGB').resize((1200,675));r=Image.open('r_match.png').convert('RGB').resize((1200,675))
R={'ses':(570,225,890,325),'ws':(820,270,1200,520),'nw':(0,260,220,460),'north':(360,230,620,330),'wbcc':(810,265,920,345)}
for k,b in R.items():
    w,h=b[2]-b[0],b[3]-b[1];s=max(1,min(4,900//w));a=ph.crop(b).resize((w*s,h*s),Image.LANCZOS);c=r.crop(b).resize((w*s,h*s),Image.LANCZOS)
    o=Image.new('RGB',(w*s*2+10,h*s+30),(20,20,20));o.paste(a,(0,30));o.paste(c,(w*s+10,30));d=ImageDraw.Draw(o)
    d.text((5,8),k+': photo',fill=(255,255,255));d.text((w*s+15,8),k+': render',fill=(255,255,255));o.save(f'crop_{k}.png')
