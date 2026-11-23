from PIL import Image, ImageDraw
a=Image.open('out/adelaide/map/whole_3km.png').convert('RGB');b=Image.open('data/adelaide/sat.png').convert('RGB'); bw=b.size[0]; b=b.crop((int(bw*100/3200),)*2+(int(bw*3100/3200),)*2).resize(a.size)
W=a.size[0]; s=W/3000.0; c=W/2; h=400*s
box=tuple(int(v) for v in (c-h,c-h,c+h,c+h))
o=Image.new('RGB',(1600,800))
for i,im in enumerate((a,b)):
    t=im.crop(box).resize((800,800)); d=ImageDraw.Draw(t)
    for m in range(-400,401,100):
        p=(m+400); d.line([(p,0),(p,800)],fill=(255,255,0)); d.line([(0,p),(800,p)],fill=(255,255,0))
    o.paste(t,(800*i,0))
o.save('out/adelaide/map/board_centre.jpg',quality=88)
