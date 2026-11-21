from PIL import Image
a=Image.open('out/peoplefirst/vs16/o_001.png').convert('RGB'); b=Image.open('out/peoplefirst/vs64/o_001.png').convert('RGB')
W,H=a.size; box=(int(W*.3),int(H*.25),int(W*.7),int(H*.6))
ca,cb=a.crop(box),b.crop(box)
s=Image.new('RGB',(ca.width*2*2,ca.height*2)); s.paste(ca.resize((ca.width*2,ca.height*2),Image.NEAREST),(0,0)); s.paste(cb.resize((cb.width*2,cb.height*2),Image.NEAREST),(ca.width*2,0)); s.save('out/peoplefirst/s16_vs_s64.png'); print(box)
