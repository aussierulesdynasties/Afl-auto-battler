from PIL import Image,ImageDraw
G='dl/moorabbin-old-grandstands1.jpg';G3='dl/moorabbin-old-grandstands3.jpg'
rows=[('huggins_blue_front',G,(150,385,930,505)),('huggins_blue',G,(330,390,700,480)),('huggins_green',G,(380,270,800,345)),
      ('pavilion',G,(420,280,700,330)),('longstand',G3,(230,150,960,542)),('longstand_close',G3,(560,300,960,542))]
def fit(im):
    im=im.resize((max(1,round(im.width*340/im.height)),340));x=max(0,(im.width-610)//2);return im.crop((x,0,x+610,340))
H=40;out=Image.new('RGB',(1240,H+len(rows)*350),(30,30,30));d=ImageDraw.Draw(out)
d.text((10,12),"Seat height: render (left) vs 1993 photo crop (right). Huggins 720 blue + 1274 green moulded shells, pavilion 245, long stand 2540 m of benches",fill=(255,255,255))
for i,(n,src,c) in enumerate(rows):
    y=H+i*350;out.paste(fit(Image.open(f'proof/seat_{n}.png').convert('RGB')),(5,y));out.paste(fit(Image.open(src).convert('RGB').crop(c)),(625,y))
    d.text((12,y+6),n,fill=(255,255,0))
out.save('proof/seats_vs_photo.png');print('ok')
