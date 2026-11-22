from PIL import Image
O='out/accor/'
ims=[Image.open(O+'stills/orbit_%03d.png'%i).convert('RGB').resize((800,450)) for i in range(4)]
s=Image.new('RGB',(1600,900))
for i,im in enumerate(ims): s.paste(im,((i%2)*800,(i//2)*450))
s.save(O+'stills/sheet.jpg',quality=88)
t=Image.open(O+'ortho/top.png').convert('RGB'); print(t.size)
t.crop((t.width//3,t.height//3,2*t.width//3,2*t.height//3)).resize((1400,1400)).save(O+'ortho/top_1km.jpg',quality=85)
