from PIL import Image, ImageDraw
a=Image.open('out/peoplefirst/water_lost.png'); g=Image.open('data/peoplefirst/sat2.png').convert('RGB')
pts=[(366,577),(600,621),(-478,522),(609,-466),(456,467),(-501,-672)]
B=Image.new('RGB',(1500,1000))
for i,(x,y) in enumerate(pts):
    px,py=x+700,700-y; b=(px-60,py-60,px+60,py+60)
    X=(i%3)*500; Y=(i//3)*500
    B.paste(a.crop(b).resize((240,240)),(X,Y+20)); B.paste(g.crop(b).resize((240,240)),(X+250,Y+20))
    ImageDraw.Draw(B).text((X,Y),'%d,%d'%(x,y),fill='yellow')
B.save('out/peoplefirst/lost_tiles.png')
