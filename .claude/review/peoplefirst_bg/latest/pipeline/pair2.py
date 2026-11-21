from PIL import Image
a=Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400)); b=Image.open('data/peoplefirst/sat2.png').convert('RGB')
B=Image.new('RGB',(1600,800))
for i,(x,y) in enumerate([(-521,-645),(-686,-276)]):
    px,py=x+700,700-y; bx=(px-100,py-100,px+100,py+100)
    B.paste(a.crop(bx).resize((400,400)),(i*800,0)); B.paste(b.crop(bx).resize((400,400)),(i*800+400,0))
B.paste(a.resize((700,400)),(0,400)); B.paste(b.resize((700,400)),(800,400))
B.save('out/peoplefirst/sat_pair.png')
