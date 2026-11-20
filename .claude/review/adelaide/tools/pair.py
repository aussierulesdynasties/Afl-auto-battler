import sys;from PIL import Image
r=Image.open(sys.argv[1]).convert('RGBA');ph=Image.open('photos/crop.jpg').convert('RGBA')
c=tuple(int(v) for v in sys.argv[3].split(',')) if len(sys.argv)>3 else (60,450,1560,1150)
a=r.crop(c);b=ph.crop(c)
o=Image.new('RGB',(a.width,a.height*2));o.paste(Image.alpha_composite(Image.new('RGBA',a.size,(0,0,0,255)),a).convert('RGB'),(0,0));o.paste(b.convert('RGB'),(0,a.height));o.save(sys.argv[2])
