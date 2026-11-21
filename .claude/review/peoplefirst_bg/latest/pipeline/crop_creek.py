from PIL import Image
t=Image.open('out/peoplefirst/ortho/top.png').convert('RGB'); s=Image.open('out/peoplefirst/ov/sat1400.png').convert('RGB').resize((1400,1400))
B=Image.new('RGB',(1200,400))
for i,(x,y) in enumerate([(-521,-645),(-295,-691),(487,-688)]):
    px,py=x+700,700-y; b=(px-50,py-50,px+50,py+50)
    B.paste(s.crop(b).resize((200,200)),(i*400,0)); B.paste(t.crop(b).resize((200,200)),(i*400+200,0))
    b=(px-50,py-50,px+50,py+50)
B.save('out/peoplefirst/creek_cmp.png')
